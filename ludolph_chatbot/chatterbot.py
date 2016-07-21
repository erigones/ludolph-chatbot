"""
This file is part of Ludolph: ChatBot
Copyright (C) 2016 Erigones, s. r. o.

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
    default_storage_adapter = 'chatterbot.adapters.storage.JsonDatabaseAdapter'
    default_logic_adapters = ('chatterbot.adapters.logic.MathematicalEvaluation,'
                              'chatterbot.adapters.logic.TimeLogicAdapter,'
                              'chatterbot.adapters.logic.ClosestMatchAdapter')

    def __init__(self, *args, **kwargs):
        super(Chatterbot, self).__init__(*args, **kwargs)
        # The chatterbot module is not listed in setup.py dependencies because this plugin supports multiple
        # chatbot modules/services. An ImportError during runtime will disable this plugin.
        # noinspection PyPackageRequirements
        from chatterbot import ChatBot

        self.chatbot_cls = ChatBot
        self.chatbot = None
        self._training_lock = False

    def __post_init__(self):
        config = self.config
        self.chatbot = self.chatbot_cls(
            self.xmpp.nick,
            input_adapter='chatterbot.adapters.input.VariableInputTypeAdapter',
            output_adapter='chatterbot.adapters.output.OutputFormatAdapter',
            storage_adapter=config.pop('storage_adapter', Chatterbot.default_storage_adapter).strip(),
            logic_adapters=config.pop('logic_adapters', Chatterbot.default_logic_adapters).strip().split(','),
            **config
        )
        logger.info('Chatterbot plugin was successfully initialized')
        logger.info('Replacing default fallback_message with chatbot response handler')
        self._original_fallback_message = self.xmpp.fallback_message
        self.xmpp.fallback_message = self._fallback_message

    def __destroy__(self):
        self.xmpp.fallback_message = self._original_fallback_message
        self.chatbot = None

    # noinspection PyUnusedLocal
    def _fallback_message(self, msg, cmd_name):
        """Fallback message handler called in case the command does not exist"""
        txt = msg.get('body', '').strip()
        start_time = time.time()
        res = self.chatbot.get_response(txt)
        logger.info('Found chatbot response in %g seconds: "%s" -> "%s"', (time.time() - start_time), txt, res.text)
        self.xmpp.msg_reply(msg, res.text)

    # noinspection PyUnusedLocal
    @command(stream_output=True)
    def chatbot_train(self, msg, *args):
        """
        Train the ChatBot by loading a corpus or reading a conversation.

        Usage (corpus): chatbot-train <python.path.to.a.corpus>
        Usage (conversation): chatbot-train "<sentence1>" "<sentence2>" "[sentence3]" ...
        """
        # noinspection PyPackageRequirements
        from chatterbot.training.trainers import ListTrainer, ChatterBotCorpusTrainer

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
