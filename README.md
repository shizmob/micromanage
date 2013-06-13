micromanage
===========

An AFK streamer, IRC bot and metadata updater.

Usage
-----
Install the requirements (`pip -r requirements.txt`).
Edit `micromanage/config.py` and start it by executing `python micromanage`.

Requirements
------------
* Python 2.x
  - Twisted
  - pyOpenSSL
  - lxml with `etree`
  - BeautifulSoup
  - pylibshout
  - tagpy

In order for stream takeover by the AFK streamer to work properly, an Icecast proxy like [icecast-proxy-go](https://github.com/Wessie/icecast-proxy-go.git) is required.

License
--------
`micromanage` is licensed under the WTFPL: see the `LICENSE` file for details.
