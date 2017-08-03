"""
This file is part of Ludolph: ChatBot
Copyright (C) 2016-2017 Erigones, s. r. o.

See the LICENSE file for copying permission.
"""
from __future__ import absolute_import

import time
import logging

from ludolph_chatbot import __version__
from ludolph.command import CommandError, MissingParameter, command
from ludolph.plugins.plugin import LudolphPlugin

logger = logging.getLogger(__name__)


class Chatterbot(LudolphPlugin):
    """
    Ludolph: ChatterBot plugin.
    """
    __version__ = __version__
    default_storage_adapter = 'chatterbot.storage.SQLStorageAdapter'
    default_logic_adapters = ('chatterbot.logic.MathematicalEvaluation,'
                              'chatterbot.logic.TimeLogicAdapter,'
                              'chatterbot.logic.BestMatch')
    default_low_confidence_threshold = 0.65
    default_low_confidence_response = 'I am sorry, but I do not understand. Check out help for chatbot-train command.'
    default_muc = False
    default_muc_confidence_threshold = 0.95

    def __init__(self, *args, **kwargs):
        super(Chatterbot, self).__init__(*args, **kwargs)
        # The chatterbot module is not listed in setup.py dependencies because this plugin supports multiple
        # chatbot modules/services. An ImportError during runtime will disable this plugin.
        # noinspection PyPackageRequirements
        from chatterbot import ChatBot
        from chatterbot.conversation.session import Session

        self.chatbot_cls = ChatBot
        self.session_cls = Session
        self.chatbot = None
        self._training_lock = False

    def __post_init__(self):
        config = self.config
        logic_adapters = config.pop('logic_adapters', self.default_logic_adapters).strip().split(',')
        storage_adapters = config.pop('storage_adapter', self.default_storage_adapter).strip()

        if 'low_confidence_threshold' in config or 'low_confidence_response' in config:
            logic_adapters.append({
                'import_path': 'chatterbot.logic.LowConfidenceAdapter',
                'threshold': float(config.pop('low_confidence_threshold', self.default_low_confidence_threshold)),
                'default_response': config.pop('low_confidence_response', self.default_low_confidence_response)
            })
        logger.debug('Chatterbot loaded storage adapters: %s', storage_adapters)
        logger.debug('Chatterbot loaded logic adapters: %s', logic_adapters)
        # MUC-related options
        self.muc = self.get_boolean_value(config.pop('muc', self.default_muc))
        self.muc_confidence_threshold = float(config.pop('muc_confidence_threshold',
                                                         self.default_muc_confidence_threshold))
        # Chatterbot instance
        self.chatbot = self.chatbot_cls(
            self.xmpp.nick,
            input_adapter='chatterbot.input.VariableInputTypeAdapter',
            output_adapter='chatterbot.output.OutputAdapter',
            storage_adapter=storage_adapters,
            logic_adapters=logic_adapters,
            **config
        )
        logger.info('Chatterbot plugin was successfully initialized')
        # Override default bot_command_not_found message handler
        self.xmpp.register_event_handler('bot_command_not_found', self._command_not_found, clear=True)

        if self.muc:  # Register to the muc_message event to watch messages in a chat room
            if self.xmpp.room:
                logger.info('Enabling chatterbot in MUC room: %s', self.xmpp.room)
                self.xmpp.register_event_handler('muc_message', self._muc_message)
            else:
                logger.warning('Chatterbot won\'t be active in a MUC room because MUC support is disabled')

    def __destroy__(self):
        # Remove our bot_command_not_found event handler
        self.xmpp.deregister_event_handler('bot_command_not_found', self._command_not_found)
        self.chatbot = None

    def _get_chat_session(self, msg):
        """Return a chatterbot session object for a user (JID)"""
        jid = self.xmpp.get_jid(msg)
        chat_session = self.chatbot.conversation_sessions.get(jid, None)

        if not chat_session:
            chat_session = self.session_cls()
            chat_session.id_string = jid
            self.chatbot.conversation_sessions.sessions[jid] = chat_session

        return chat_session

    # noinspection PyUnusedLocal
    def _command_not_found(self, msg, cmd_name):
        """Message handler called in case the command does not exist"""
        if not self.xmpp.is_jid_user(self.xmpp.get_jid(msg)):
            return

        try:
            chat_session = self._get_chat_session(msg)
            txt = msg.get('body', '').strip()
            start_time = time.time()
            res = self.chatbot.get_response(txt, session_id=chat_session.id_string)
            reply = res.text
            logger.info('Found chatbot response (with confidence %s) in %g seconds: "%s" -> "%s"',
                        res.confidence, (time.time() - start_time), txt, reply)
        except Exception as exc:
            reply = 'ERROR: Chatbot malfunction (%s)' % exc
            logger.exception(exc)

        self.xmpp.msg_reply(msg, reply)

    def _muc_message(self, msg):
        """MUC message handler called when someone says something in a MUC room"""
        # Ignore messages from unauthorized users
        if not self.xmpp.is_jid_room_user(self.xmpp.get_jid(msg)):
            return

        chatbot = self.chatbot
        txt = msg.get('body', '').strip()

        # We are going to analyze the whole user message as it appeared in the chat room
        # We don't want to learn anything, just see if we are confident enough to post a reply into the room
        try:
            start_time = time.time()
            # The next lines are taken from ChatBot.get_response()
            session_id = str(chatbot.default_session.uuid)
            input_statement = chatbot.input.process_input_statement(txt)

            for preprocessor in chatbot.preprocessors:
                input_statement = preprocessor(chatbot, input_statement)

            statement, response = chatbot.generate_response(input_statement, session_id)

            if response.confidence > self.muc_confidence_threshold:
                chatbot.conversation_sessions.update(session_id, (statement, response,))
                res = chatbot.output.process_response(response, session_id)
                reply = res.text
                logger.info('Found chatbot response in MUC room (with confidence %s) in %g seconds: "%s" -> "%s"',
                            res.confidence, (time.time() - start_time), txt, reply)
                self.xmpp.msg_reply(msg, reply)
        except Exception as exc:
            logger.error('Chatbot malfunction in MUC room while analyzing text "%s"', txt)
            logger.exception(exc)

    # noinspection PyUnusedLocal
    @command(stream_output=True, admin_required=True)
    def chatbot_train(self, msg, *args):
        """
        Train the ChatBot by loading a corpus or reading a conversation (admin only).

        Usage (corpus): chatbot-train <python.path.to.a.corpus>
        Usage (conversation): chatbot-train "<sentence1>" "<sentence2>" "[sentence3]" ...
        """
        # noinspection PyPackageRequirements
        from chatterbot.trainers import ListTrainer, ChatterBotCorpusTrainer

        if not args:
            raise MissingParameter

        if not self.chatbot:
            raise CommandError('ChatBot is not initialized')

        if len(args) > 1:
            trainer_cls = ListTrainer
            data = args
        else:
            trainer_cls = ChatterBotCorpusTrainer
            data = args[0]

        if self._training_lock:
            raise CommandError('Training in progress')

        self._training_lock = True

        try:
            self.chatbot.set_trainer(trainer_cls)
            yield 'Starting training from <%s:%s>' % (trainer_cls.__name__, data)

            try:
                self.chatbot.train(data)
            except Exception as exc:
                raise CommandError('Training failed: %s' % exc)
            else:
                yield 'Finished training from <%s:%s>' % (trainer_cls.__name__, data)
        finally:
            self._training_lock = False
