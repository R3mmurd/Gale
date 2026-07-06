# Rally

A small online Pong built to exercise `gale.net` (LAN/internet
multiplayer over a hand-rolled reliable UDP layer) and `gale.ui`
(menus, text entry, buttons) together. Two players, real-time paddles
and ball, works whether they're on the same LAN or not.

## Running it

From the repository root, install gale itself in editable mode so it's
importable from anywhere (only needed once):

```bash
pip install -e .
```

Then run two copies of the game (two terminals, or two machines on the
same network):

```bash
cd examples/rally
python main.py
```

One player picks **Host Game**, the other picks **Join Game** and
either types the host's `ip:port` or clicks **Scan LAN** to find it
automatically (LAN only). To play against yourself locally, host in
one window and join at `127.0.0.1:9000` in another.

## Controls

- `Up`/`W`, `Down`/`S`: move your paddle
- `Enter`: confirm the highlighted menu item
- Mouse: click menu items, type in text fields
- `Escape`: quit

## How it plays

- `TitleState`: Host Game / Join Game / Quit, built with `gale.ui`.
- `LobbyState`: as host, opens a `gale.net.Server` and waits for one
  opponent (also answering LAN discovery requests so **Scan LAN**
  finds it); as the joining player, connects a `gale.net.Client` to a
  typed or discovered address.
- `PlayState`: the host is authoritative — it simulates the ball and
  both paddles and broadcasts a `"snapshot"` (`Channel.UNRELIABLE`,
  since a dropped one is harmless: the next one supersedes it) every
  frame, plus `"score"`/`"game_over"` events on
  `Channel.RELIABLE_UNORDERED` (those must not be lost). Both sides
  render their own paddle immediately from local input; the joining
  client renders the opponent's paddle and the ball from
  `src/snapshot_buffer.py`, a small buffered-interpolation recipe (not
  part of `gale.net` itself — see its docstring) driven by
  `Client.get_rtt()`. A `"ping: N ms"` HUD label shows that RTT live.
- `GameOverState`: final score, a button back to the title screen.

## What it uses

- `gale.net.Server`/`gale.net.Client`: the connection itself, message
  send/broadcast/receive, and `discover_lan_servers` for the LAN scan.
- `gale.ui`: `Container`, `Panel`, `Label`, `Button`, `ListView`,
  `TextInput`, and `UIManager` for every menu/HUD element.
- `gale.state.BaseState`/`StateMachine`, `gale.timer.Timer`,
  `gale.text.render_text`, same as the other examples.

## `dedicated_server.py`

A separate, pygame-free script that only imports `gale.net`, meant to
run on a machine with no display at all:

```bash
python dedicated_server.py 9000
```

It runs its **own** small authoritative simulation for two remote
players, so it is not wire-compatible with `PlayState`'s player-hosted
protocol above (there, the host plays too and is always "left"; here,
neither connecting player is local, so the server assigns each one a
side via an `"assign_side"` message and broadcasts both paddles in
every snapshot). Extending `LobbyState`'s Join flow to speak this
second protocol (learn your assigned side, read both paddles out of
each snapshot instead of owning one locally) is a natural follow-up,
not currently wired into the menus.

## Known limitations

- No NAT traversal: internet play needs a reachable `host:port` (a
  public server, a cloud VM, or a port-forwarded host).
- No client-side prediction/reconciliation: the joining player's own
  paddle is rendered from its own input with no correction from the
  host, so a very high-latency connection can make the two players'
  views of that paddle drift apart slightly. Good enough for a casual
  match; a competitive game would want real reconciliation.
- `TextInput` (used for the "host:port" field) only supports ASCII
  input, not IME/composed characters — see `gale.ui.TextInput`'s
  docstring.
