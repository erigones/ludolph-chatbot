ludolph-chatbot
###############

`Ludolph <https://github.com/erigones/Ludolph>`_: ChatBot plugin.

Plugin that allows a machine-learning based conversational dialog engine.
Although it currently uses the `ChatterBot <https://github.com/gunthercox/ChatterBot>`_ engine it can be easily extended to support other dialog engines.

**Plugin is not production ready yet.**

Installation
------------

- Install the latest released version using pip::

    pip install https://github.com/erigones/ludolph-chatbot/tarball/master

- Add new plugin section into Ludolph configuration file (see configuration section for more options)::

    [ludolph_chatbot.chatterbot]
    database = /var/lib/ludolph/ludolph_chatbot.sqlite3

- Reload Ludolph::

    service ludolph reload


**Dependencies:**

- `Ludolph <https://github.com/erigones/Ludolph>`_ (0.9.0+)
- `ChatterBot <https://github.com/gunthercox/ChatterBot>`_ (0.7.4+)


Configuration
-------------

Optional config options and its default values.
These options can be defined in the config file to change ChatBot plugin behaviour.

logic_adapters
~~~~~~~~~~~~~~

- ``logic_adapters = chatterbot.logic.MathematicalEvaluation,chatterbot.logic.TimeLogicAdapter,chatterbot.logic.BestMatch``
- ``storage_adapter = chatterbot.storage.SQLStorageAdapter``
- ``low_confidence_threshold = 0.65``
- ``low_confidence_response = I am sorry, but I do not understand. Check out help for chatbot-train command.``
- ``muc = false``
- ``muc_confidence_threshold = 0.95``

To enable the LowConfidenceAdapter just define ``low_confidence_threshold`` or ``low_confidence_response`` in your `Ludolph <https://github.com/erigones/Ludolph>`_ configuration file.


Links
-----

- Wiki: https://github.com/erigones/Ludolph/wiki/How-to-create-a-plugin#create-3rd-party-plugin
- Bug Tracker: https://github.com/erigones/ludolph-chatbot/issues
- Google+ Community: https://plus.google.com/u/0/communities/112192048027134229675
- Twitter: https://twitter.com/erigones


License
-------

For more information see the `LICENSE <https://github.com/erigones/ludolph-chatbot/blob/master/LICENSE>`_ file.
