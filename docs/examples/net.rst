`← Back to the main README <../../README.rst>`_

gale.net
========

``gale.net`` is a pure-Python, pygame-free toolkit for LAN or internet
multiplayer: a ``Server`` and a ``Client`` talking over a single UDP
socket each, with a small hand-rolled reliability layer for the
messages that must not be lost, and automatic per-peer round-trip-time
(RTT) tracking. See ``examples/rally`` for a full game (an online
Pong) built on top of it.

Basic connection and messaging
-------------------------------

.. code-block:: python

   from gale.net.server import Server
   from gale.net.client import Client

   server = Server(port=9000)
   server.on_connect(lambda peer: print(f"peer {peer.peer_id} connected"))
   server.on_message("hello", lambda peer, payload: print(peer.peer_id, payload))

   client = Client()
   client.on_connect(lambda: print("connected"))
   client.connect("127.0.0.1", 9000)

   # In your game loop, every frame:
   server.update(dt)
   client.update(dt)

   # Once client.connected is True:
   client.send("hello", {"name": "Ada"})
   server.broadcast("welcome", {"message": "hi!"})

``connect``/message sending never block: outcomes and incoming
messages always surface later, through the callbacks registered with
``on_connect``/``on_connect_failed``/``on_disconnect``/``on_message``,
the next time you call ``update(dt)``.

Choosing a channel
-------------------

Every send takes a ``channel`` (default ``Channel.UNRELIABLE``):

.. list-table::
   :header-rows: 1

   * - Channel
     - Use it for
   * - ``Channel.UNRELIABLE``
     - State that's superseded by the next update anyway (a position snapshot sent every frame) — a lost packet is harmless.
   * - ``Channel.RELIABLE_ORDERED``
     - Events where both delivery and order matter (a chat log, a sequence of moves in a board game).
   * - ``Channel.RELIABLE_UNORDERED``
     - Events that must not be lost but don't depend on each other (a "point scored" or "player joined" notification) — cheaper than ordered, since it never holds a packet back waiting for an earlier one.

.. code-block:: python

   from gale.net.protocol import Channel

   server.broadcast("snapshot", {"x": x, "y": y}, channel=Channel.UNRELIABLE)
   server.broadcast("score", {"points": 10}, channel=Channel.RELIABLE_UNORDERED)

Round-trip time
-----------------

Both sides measure it automatically (a small ping/pong exchanged every
``heartbeat_interval`` seconds):

.. code-block:: python

   client.get_rtt()               # this client's RTT to the server, in seconds, or None
   server.get_rtt(peer.peer_id)    # the server's RTT to a given peer, or None

Use it to size a client-side interpolation delay, show a "ping: N ms"
HUD label, or decide when a connection is bad enough to warn the
player — ``examples/rally`` does all three (see
``examples/rally/src/snapshot_buffer.py``).

LAN discovery
--------------

So a joining player doesn't have to type an IP address:

.. code-block:: python

   server.enable_lan_discovery("My Game Server")

   from gale.net.discovery import discover_lan_servers

   found = discover_lan_servers(timeout=1.0)  # -> List[ServerInfo]

Relies on IP broadcast, so it only ever finds servers on the same
local network — never call ``enable_lan_discovery`` on a public,
internet-facing dedicated server (tiny request/response packets kept
LAN-only avoid it being useful as an amplification vector).

Dedicated server vs. player-hosted
------------------------------------

The same ``Server`` class covers both:

- **Player-hosted**: one player's own game process creates the
  ``Server`` (and usually plays too, driving its own state locally
  rather than through the network — see how ``examples/rally``'s host
  simulates the ball/paddles directly and just broadcasts the result).
- **Dedicated server**: a separate, pygame-free script imports only
  ``gale.net`` and runs its own loop:

  .. code-block:: python

     import time
     from gale.net.server import Server

     server = Server(port=9000)

     while True:
         server.update(1 / 60)
         time.sleep(1 / 60)

  See ``examples/rally/dedicated_server.py`` for a complete one.

Host migration
----------------

Not a built-in feature (it is inherently game-specific: who becomes
the new host, and how much state they need to reconstruct, varies a
lot), but straightforward to build from the existing primitives. A
common recipe: every peer already knows every other peer's
``peer_id`` (increasing, never reused within a ``Server``'s lifetime)
through ``on_connect``, so on ``on_disconnect`` for the current host,
whichever remaining peer has the lowest ``peer_id`` starts a new
``Server`` and everyone else reconnects to it.

Room codes
-----------

Sharing a raw IP and port with a friend is fiddly and easy to
mistype. ``encode``/``decode`` turn a ``(host, port)`` pair into a
short, human-typeable code and back — a *local, symmetric encoding*,
not a matchmaking service: there is no server involved, and no
dependency on ``Server``/``Client``:

.. code-block:: python

   from gale.net import encode, decode

   code = encode(public_ip, server.port)  # e.g. "7QK3M-2XHDR"
   # ... shared with a friend, over voice chat or a chat message ...
   host, port = decode(code)
   client.connect(host, port)

``decode`` ignores whitespace, the group separator, and (for a
same-case alphabet, as the default is) letter case, so
``"7qk3m 2xhdr"`` decodes the same as ``"7QK3M-2XHDR"``. The default
format is Crockford's base32 (excludes ``I``, ``L``, ``O``, ``U`` to
avoid transcription mistakes) in two groups of 5.

Every part of the format is configurable per game through
``RoomCodeFormat``, so a game can match its own house style instead of
the default:

.. code-block:: python

   from gale.net import RoomCodeFormat, encode, decode

   # e.g. "7qk3-m2xh-dr" style: lowercase, 4-4-2 groups, dash-separated.
   my_format = RoomCodeFormat(
       alphabet="0123456789abcdefghjkmnpqrstvwxyz",
       group_size=4,
   )
   code = encode(public_ip, server.port, my_format)
   host, port = decode(code, my_format)

``host`` accepts either an IPv4 address or a resolvable hostname (in
which case ``encode`` resolves it once, at encoding time, to bake the
resulting address into the code). This is purely about turning an
address into a shareable string: getting the right address to encode
in the first place (the LAN address, the public address behind a
NAT/router, and picking between the two) is up to the game, the same
way ``gale.net`` never picks between LAN discovery and a direct
connection for you.

Security notes
----------------

- Each connection gets a random token (via ``secrets.randbits``)
  echoed in every packet, rejecting packets whose token doesn't match
  the address they claim to come from. This guards against casual UDP
  source-address spoofing, not a determined on-path attacker — there
  is no encryption or authentication beyond this.
- Retransmit attempts, in-flight unacked packets per peer, and
  incoming datagram size are all capped, so a slow/hostile peer can't
  grow a ``Server``'s memory without bound.
- Malformed/unparseable incoming data is dropped, never raised out of
  ``update()``.
