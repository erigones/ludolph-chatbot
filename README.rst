ludolph-chatbot
###############

`Ludolph <https://github.com/erigones/Ludolph>`_: ChatBot plugin.

Plugin that allows a machine-learning based conversational dialog engine.
Although it currently uses the `ChatterBot <https://github.com/gunthercox/ChatterBot>_` engine it can be easily extended to support other dialog engines.
**Plugin is not production ready yet.**

Installation
------------

- Install the latest released version using pip::

    pip install https://github.com/erigones/ludolph-chatbot/tarball/master

- Add new plugin section into Ludolph configuration file::

    [ludolph_chatbot.chatterbot]
    database = /var/lib/ludolph/ludolph_chatbot.db

- Reload Ludolph::

    service ludolph reload


**Dependencies:**

- `Ludolph <https://github.com/erigones/Ludolph>`_ (0.9.0+)
- `ChatterBot <https://github.com/gunthercox/ChatterBot>`_ (0.4.10+)


Links
-----

- Wiki: https://github.com/erigones/Ludolph/wiki/How-to-create-a-plugin#create-3rd-party-plugin
- Bug Tracker: https://github.com/erigones/ludolph-chatbot/issues
- Google+ Community: https://plus.google.com/u/0/communities/112192048027134229675
- Twitter: https://twitter.com/erigones


License
-------

For more information see the `LICENSE <https://github.com/erigones/ludolph-chatbot/blob/master/LICENSE>`_ file.
