"""
This file contains the implementation of the class Server, the
listening/authoritative side of a gale.net connection.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import json
import secrets
import socket
import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from .channel import ReliableReceiver, ReliableSender
from .discovery import DEFAULT_DISCOVERY_PORT, DISCOVERY_MAGIC
from .peer import Peer
from .protocol import (
    ACK,
    CONNECT_ACCEPTED,
    CONNECT_REQUEST,
    DISCONNECT,
    HEADER_SIZE,
    MAX_PAYLOAD_SIZE,
    PING,
    PONG,
    Channel,
    pack_header,
    unpack_header,
)
from .serialization import Deserializer, Serializer, json_deserialize, json_serialize

MAX_DATAGRAM_SIZE: int = HEADER_SIZE + MAX_PAYLOAD_SIZE + 64

OnConnect = Callable[[Peer], None]
OnDisconnect = Callable[[Peer], None]
OnMessage = Callable[[Peer, Dict[str, Any]], None]


class Server:
    """
    The authoritative/listening side of a gale.net game: accepts
    connections from any number of Clients over a single non-blocking
    UDP socket, and lets the game send/broadcast messages to them and
    react to the ones they send back.

    Usage example:

        server = Server(port=9000)
        server.on_connect(lambda peer: print(f"{peer.peer_id} joined"))
        server.on_message("input", lambda peer, payload: ...)

        # In the game loop:
        server.update(dt)
        server.broadcast("snapshot", {"positions": [...]})
    """

    def __init__(
        self,
        port: int,
        host: str = "0.0.0.0",
        max_peers: Optional[int] = None,
        serialize: Serializer = json_serialize,
        deserialize: Deserializer = json_deserialize,
        heartbeat_interval: float = 1.0,
        timeout: float = 5.0,
    ) -> None:
        """
        :param port: The UDP port to listen on.
        :param host: The address to bind to. The default value is "0.0.0.0" (every local interface).
        :param max_peers: Maximum number of simultaneously connected peers. The default value is None, meaning no limit.
        :param serialize: Function used to turn a (message_type, payload) pair into bytes. The default value is json_serialize.
        :param deserialize: Function used to turn received bytes back into a (message_type, payload) pair. The default value is json_deserialize.
        :param heartbeat_interval: How often, in seconds, a ping is sent to each connected peer to measure its round-trip time and detect disconnections. The default value is 1.0.
        :param timeout: How long, in seconds, without receiving anything from a peer before it is considered disconnected. The default value is 5.0.
        """
        self.max_peers: Optional[int] = max_peers
        self.timeout: float = timeout
        self.heartbeat_interval: float = heartbeat_interval

        self._serialize: Serializer = serialize
        self._deserialize: Deserializer = deserialize

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)
        self._socket.bind((host, port))
        # Reflects the actual bound port even when the caller passed
        # port=0 to let the OS pick a free one (handy for tests and for
        # running several servers on one host without hardcoding ports).
        self.port: int = self._socket.getsockname()[1]

        self._peers: Dict[int, Peer] = {}
        self._peers_by_address: Dict[Tuple[str, int], int] = {}
        self._next_peer_id: int = 1

        self._senders: Dict[Tuple[int, int], ReliableSender] = {}
        self._receivers: Dict[Tuple[int, int], ReliableReceiver] = {}

        self._on_connect_callbacks: List[OnConnect] = []
        self._on_disconnect_callbacks: List[OnDisconnect] = []
        self._on_message_callbacks: Dict[str, List[OnMessage]] = {}

        self._last_heartbeat: float = 0.0
        self._next_ping_id: int = 0
        self._ping_sent_at: Dict[int, float] = {}
        self._ping_peer: Dict[int, int] = {}

        self._discovery_socket: Optional[socket.socket] = None
        self._discovery_name: str = ""

    def on_connect(self, callback: OnConnect) -> None:
        """
        :param callback: Called with the new Peer every time a Client connects.
        """
        self._on_connect_callbacks.append(callback)

    def on_disconnect(self, callback: OnDisconnect) -> None:
        """
        :param callback: Called with the Peer every time a connected Client disconnects (explicitly or by timing out).
        """
        self._on_disconnect_callbacks.append(callback)

    def on_message(self, message_type: str, callback: OnMessage) -> None:
        """
        :param message_type: The message type to react to.
        :param callback: Called with (peer, payload) every time a message of this type is received from any peer.
        """
        self._on_message_callbacks.setdefault(message_type, []).append(callback)

    def enable_lan_discovery(
        self, name: str, discovery_port: int = DEFAULT_DISCOVERY_PORT
    ) -> None:
        """
        Start answering LAN discovery requests (see gale.net.discovery)
        so a Client can find this Server without knowing its address
        ahead of time. Only meant for servers reachable on a local
        network: do not call this on a public, internet-facing
        dedicated server.

        :param name: The name shown to clients discovering this server.
        :param discovery_port: The UDP port to listen for discovery requests on. The default value is DEFAULT_DISCOVERY_PORT.
        """
        self._discovery_name = name
        self._discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._discovery_socket.setblocking(False)
        self._discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._discovery_socket.bind(("0.0.0.0", discovery_port))

    def get_peers(self) -> List[Peer]:
        """
        :returns: The list of currently connected peers.
        """
        return list(self._peers.values())

    def get_rtt(self, peer_id: int) -> Optional[float]:
        """
        :param peer_id: The peer to query.
        :returns: The peer's smoothed round-trip time in seconds, or None if peer_id is not connected.
        """
        peer = self._peers.get(peer_id)
        return peer.rtt if peer is not None else None

    def send_to(
        self,
        peer_id: int,
        message_type: str,
        payload: Dict[str, Any],
        channel: int = Channel.UNRELIABLE,
    ) -> None:
        """
        :param peer_id: The peer to send to.
        :param message_type: The message type.
        :param payload: The message data.
        :param channel: One of the Channel constants. The default value is Channel.UNRELIABLE.
        """
        peer = self._peers.get(peer_id)

        if peer is not None:
            self._send(peer, channel, message_type, payload)

    def broadcast(
        self,
        message_type: str,
        payload: Dict[str, Any],
        channel: int = Channel.UNRELIABLE,
        exclude: Optional[Iterable[int]] = None,
    ) -> None:
        """
        :param message_type: The message type.
        :param payload: The message data.
        :param channel: One of the Channel constants. The default value is Channel.UNRELIABLE.
        :param exclude: Peer ids to skip. The default value is None.
        """
        excluded = set(exclude) if exclude is not None else set()

        for peer in list(self._peers.values()):
            if peer.peer_id not in excluded:
                self._send(peer, channel, message_type, payload)

    def disconnect(self, peer_id: int) -> None:
        """
        :param peer_id: The peer to disconnect.
        """
        peer = self._peers.get(peer_id)

        if peer is not None:
            self._remove_peer(peer)

    def close(self) -> None:
        """
        Close the underlying sockets. The server is no longer usable afterwards.
        """
        self._socket.close()

        if self._discovery_socket is not None:
            self._discovery_socket.close()

    def update(self, dt: float) -> None:
        """
        Poll the network and drive every peer's connection state:
        receive and dispatch messages, retransmit unacked reliable
        packets, send heartbeats, and detect timed-out peers.

        :param dt: Time elapsed, in seconds, since the last call. Currently unused (timing is wall-clock based), accepted for consistency with the rest of gale.
        """
        now = time.monotonic()
        self._poll_socket(now)
        self._poll_discovery()
        self._run_heartbeat(now)
        self._run_reliability(now)
        self._check_timeouts(now)

    def _poll_socket(self, now: float) -> None:
        while True:
            try:
                data, address = self._socket.recvfrom(MAX_DATAGRAM_SIZE)
            except BlockingIOError:
                return
            except OSError:
                return

            self._handle_packet(data, address, now)

    def _handle_packet(self, data: bytes, address: Tuple[str, int], now: float) -> None:
        try:
            channel, token, sequence, ack, ack_bitfield = unpack_header(data)
            body = data[HEADER_SIZE:]
            message_type, payload = self._deserialize(body)
        except Exception:
            return

        peer_id = self._peers_by_address.get(address)

        if peer_id is None:
            if message_type == CONNECT_REQUEST:
                self._accept_connection(address, now)
            return

        if message_type == CONNECT_REQUEST:
            # The client is retrying because it never saw our
            # CONNECT_ACCEPTED reply (it was lost); resend it rather
            # than silently dropping the retry on the token check below.
            self._resend_accept(self._peers[peer_id])
            return

        peer = self._peers[peer_id]

        if token != peer.token:
            return

        peer.last_seen = now
        is_reliable = channel in (Channel.RELIABLE_ORDERED, Channel.RELIABLE_UNORDERED)

        if is_reliable:
            self._get_sender(peer_id, channel).acknowledge(ack, ack_bitfield)

        if message_type == PING:
            self._send(peer, Channel.UNRELIABLE, PONG, payload)
            return

        if message_type == PONG:
            ping_id = payload.get("id")
            sent_at = self._ping_sent_at.pop(ping_id, None)
            self._ping_peer.pop(ping_id, None)

            if sent_at is not None:
                peer.update_rtt(now - sent_at)

            return

        if message_type == ACK:
            # Its only purpose was to carry the ack/ack_bitfield header
            # fields applied above; it is not part of the ordered
            # stream and never consumed a sequence number.
            return

        if message_type == DISCONNECT:
            self._remove_peer(peer)
            return

        if is_reliable:
            receiver = self._get_receiver(
                peer_id, channel, ordered=channel == Channel.RELIABLE_ORDERED
            )

            for raw in receiver.receive(sequence, body):
                try:
                    inner_type, inner_payload = self._deserialize(raw)
                except Exception:
                    continue

                self._dispatch(peer, inner_type, inner_payload)
        else:
            self._dispatch(peer, message_type, payload)

    def _dispatch(self, peer: Peer, message_type: str, payload: Dict[str, Any]) -> None:
        for callback in self._on_message_callbacks.get(message_type, []):
            callback(peer, payload)

    def _accept_connection(self, address: Tuple[str, int], now: float) -> None:
        if self.max_peers is not None and len(self._peers) >= self.max_peers:
            return

        peer_id = self._next_peer_id
        self._next_peer_id += 1
        token = secrets.randbits(64)
        peer = Peer(peer_id, address, token)
        peer.last_seen = now
        self._peers[peer_id] = peer
        self._peers_by_address[address] = peer_id

        self._resend_accept(peer)

        for callback in self._on_connect_callbacks:
            callback(peer)

    def _resend_accept(self, peer: Peer) -> None:
        body = self._serialize(CONNECT_ACCEPTED, {"peer_id": peer.peer_id})
        header = pack_header(Channel.UNRELIABLE, peer.token, 0, 0, 0)
        self._socket.sendto(header + body, peer.address)

    def _run_heartbeat(self, now: float) -> None:
        if now - self._last_heartbeat < self.heartbeat_interval:
            return

        self._last_heartbeat = now

        for peer in list(self._peers.values()):
            ping_id = self._next_ping_id
            self._next_ping_id += 1
            self._ping_sent_at[ping_id] = now
            self._ping_peer[ping_id] = peer.peer_id
            self._send(peer, Channel.UNRELIABLE, PING, {"id": ping_id})

    def _run_reliability(self, now: float) -> None:
        for (peer_id, channel), sender in list(self._senders.items()):
            peer = self._peers.get(peer_id)

            if peer is None:
                continue

            due, gave_up = sender.due_for_retransmit(now, peer.rtt)

            for sequence, payload in due:
                self._send_raw(peer, channel, sequence, payload)

            if gave_up:
                self._remove_peer(peer)
                continue

            receiver = self._receivers.get((peer_id, channel))

            if receiver is not None and receiver.highest_received is not None:
                self._send_ack_only(peer, channel)

    def _check_timeouts(self, now: float) -> None:
        for peer in list(self._peers.values()):
            if now - peer.last_seen > self.timeout:
                self._remove_peer(peer)

    def _remove_peer(self, peer: Peer) -> None:
        peer.connected = False
        self._peers.pop(peer.peer_id, None)
        self._peers_by_address.pop(peer.address, None)
        self._senders = {
            key: value for key, value in self._senders.items() if key[0] != peer.peer_id
        }
        self._receivers = {
            key: value
            for key, value in self._receivers.items()
            if key[0] != peer.peer_id
        }

        for callback in self._on_disconnect_callbacks:
            callback(peer)

    def _get_sender(self, peer_id: int, channel: int) -> ReliableSender:
        key = (peer_id, channel)

        if key not in self._senders:
            self._senders[key] = ReliableSender()

        return self._senders[key]

    def _get_receiver(
        self, peer_id: int, channel: int, ordered: bool = False
    ) -> ReliableReceiver:
        key = (peer_id, channel)

        if key not in self._receivers:
            self._receivers[key] = ReliableReceiver(ordered=ordered)

        return self._receivers[key]

    def _send(
        self, peer: Peer, channel: int, message_type: str, payload: Dict[str, Any]
    ) -> None:
        body = self._serialize(message_type, payload)

        if len(body) > MAX_PAYLOAD_SIZE:
            raise ValueError(
                f"Message of type {message_type!r} is too large "
                f"({len(body)} bytes > {MAX_PAYLOAD_SIZE})"
            )

        if channel == Channel.UNRELIABLE:
            header = pack_header(channel, peer.token, 0, 0, 0)
            self._socket.sendto(header + body, peer.address)
            return

        sender = self._get_sender(peer.peer_id, channel)

        if sender.is_overflowing():
            self._remove_peer(peer)
            return

        sequence = sender.next()
        sender.track(sequence, body, time.monotonic())
        self._send_raw(peer, channel, sequence, body)

    def _send_raw(self, peer: Peer, channel: int, sequence: int, body: bytes) -> None:
        receiver = self._get_receiver(peer.peer_id, channel)
        ack, ack_bitfield = receiver.build_ack()
        header = pack_header(channel, peer.token, sequence, ack, ack_bitfield)
        self._socket.sendto(header + body, peer.address)

    def _send_ack_only(self, peer: Peer, channel: int) -> None:
        """
        Send a bare ack, outside of the reliable sequence: it never
        consumes a sequence number and is never retransmitted (a fresh
        one is sent again on the next update() anyway), it only exists
        to let the peer's ReliableSender free packets it has no other
        reason to hear about right now.
        """
        receiver = self._get_receiver(peer.peer_id, channel)
        ack, ack_bitfield = receiver.build_ack()
        body = self._serialize(ACK, {})
        header = pack_header(channel, peer.token, 0, ack, ack_bitfield)
        self._socket.sendto(header + body, peer.address)

    def _poll_discovery(self) -> None:
        if self._discovery_socket is None:
            return

        while True:
            try:
                data, address = self._discovery_socket.recvfrom(512)
            except BlockingIOError:
                return
            except OSError:
                return

            if not data.startswith(DISCOVERY_MAGIC):
                continue

            reply = DISCOVERY_MAGIC + json.dumps(
                {
                    "name": self._discovery_name,
                    "port": self.port,
                    "player_count": len(self._peers),
                }
            ).encode("utf-8")
            self._discovery_socket.sendto(reply, address)
