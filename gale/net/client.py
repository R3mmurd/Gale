"""
This file contains the implementation of the class Client, the
connecting side of a gale.net connection.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import socket
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from .channel import ReliableReceiver, ReliableSender
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

# How often, while waiting for a reply, the connect request is resent.
CONNECT_RETRY_INTERVAL: float = 0.5

OnConnect = Callable[[], None]
OnConnectFailed = Callable[[str], None]
OnDisconnect = Callable[[str], None]
OnMessage = Callable[[Dict[str, Any]], None]


class Client:
    """
    The connecting side of a gale.net game: connects to a single
    Server over a non-blocking UDP socket, and lets the game send
    messages to it and react to the ones it sends back.

    Usage example:

        client = Client()
        client.on_connect(lambda: print("connected"))
        client.on_message("snapshot", lambda payload: ...)
        client.connect("127.0.0.1", 9000)

        # In the game loop:
        client.update(dt)
        client.send("input", {"move": "left"})
    """

    def __init__(
        self,
        serialize: Serializer = json_serialize,
        deserialize: Deserializer = json_deserialize,
        timeout: float = 5.0,
    ) -> None:
        """
        :param serialize: Function used to turn a (message_type, payload) pair into bytes. The default value is json_serialize.
        :param deserialize: Function used to turn received bytes back into a (message_type, payload) pair. The default value is json_deserialize.
        :param timeout: How long, in seconds, without receiving anything from the server before it is considered disconnected. The default value is 5.0.
        """
        self.timeout: float = timeout
        self.connected: bool = False
        self.token: int = 0

        self._serialize: Serializer = serialize
        self._deserialize: Deserializer = deserialize

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)

        self._server_address: Optional[Tuple[str, int]] = None
        self._connecting: bool = False
        self._connect_timeout: float = 0.0
        self._connect_deadline: float = 0.0
        self._last_connect_attempt: float = 0.0
        self._last_seen: float = 0.0

        self._senders: Dict[int, ReliableSender] = {}
        self._receivers: Dict[int, ReliableReceiver] = {}

        self._on_connect_callbacks: List[OnConnect] = []
        self._on_connect_failed_callbacks: List[OnConnectFailed] = []
        self._on_disconnect_callbacks: List[OnDisconnect] = []
        self._on_message_callbacks: Dict[str, List[OnMessage]] = {}

        self.rtt: float = 0.0
        self._last_heartbeat: float = 0.0
        self.heartbeat_interval: float = 1.0
        self._next_ping_id: int = 0
        self._ping_sent_at: Dict[int, float] = {}

    def on_connect(self, callback: OnConnect) -> None:
        """
        :param callback: Called with no arguments once the connection is established.
        """
        self._on_connect_callbacks.append(callback)

    def on_connect_failed(self, callback: OnConnectFailed) -> None:
        """
        :param callback: Called with a reason string if connect() times out without a reply.
        """
        self._on_connect_failed_callbacks.append(callback)

    def on_disconnect(self, callback: OnDisconnect) -> None:
        """
        :param callback: Called with a reason string when a previously established connection ends, explicitly or by timing out.
        """
        self._on_disconnect_callbacks.append(callback)

    def on_message(self, message_type: str, callback: OnMessage) -> None:
        """
        :param message_type: The message type to react to.
        :param callback: Called with the payload every time a message of this type is received.
        """
        self._on_message_callbacks.setdefault(message_type, []).append(callback)

    def connect(self, host: str, port: int, timeout: float = 5.0) -> None:
        """
        Start connecting to a Server. Non-blocking: the outcome is
        reported later, through update(), via the on_connect/
        on_connect_failed callbacks.

        :param host: The server's address.
        :param port: The server's port.
        :param timeout: How long to keep retrying before giving up, in seconds. The default value is 5.0.
        """
        self._server_address = (host, port)
        self._connecting = True
        self.connected = False
        now = time.monotonic()
        self._connect_deadline = now + timeout
        self._last_connect_attempt = 0.0

    def get_rtt(self) -> Optional[float]:
        """
        :returns: The smoothed round-trip time to the server, in seconds, or None if not connected.
        """
        return self.rtt if self.connected else None

    def send(
        self,
        message_type: str,
        payload: Dict[str, Any],
        channel: int = Channel.UNRELIABLE,
    ) -> None:
        """
        :param message_type: The message type.
        :param payload: The message data.
        :param channel: One of the Channel constants. The default value is Channel.UNRELIABLE.
        """
        if not self.connected or self._server_address is None:
            return

        body = self._serialize(message_type, payload)

        if len(body) > MAX_PAYLOAD_SIZE:
            raise ValueError(
                f"Message of type {message_type!r} is too large "
                f"({len(body)} bytes > {MAX_PAYLOAD_SIZE})"
            )

        if channel == Channel.UNRELIABLE:
            header = pack_header(channel, self.token, 0, 0, 0)
            self._socket.sendto(header + body, self._server_address)
            return

        sender = self._get_sender(channel)

        if sender.is_overflowing():
            self._handle_disconnect("too many unacked reliable packets")
            return

        sequence = sender.next()
        sender.track(sequence, body, time.monotonic())
        self._send_raw(channel, sequence, body)

    def disconnect(self) -> None:
        """
        End the current connection, if any, telling the server so it
        does not have to wait for a timeout to notice. Does not notify
        this client's own on_disconnect (that is reserved for
        connections that end unexpectedly).
        """
        if self.connected and self._server_address is not None:
            header = pack_header(Channel.UNRELIABLE, self.token, 0, 0, 0)
            body = self._serialize(DISCONNECT, {})
            self._socket.sendto(header + body, self._server_address)

        self.connected = False
        self._connecting = False
        self._server_address = None
        self._senders.clear()
        self._receivers.clear()

    def close(self) -> None:
        """
        Close the underlying socket. The client is no longer usable afterwards.
        """
        self._socket.close()

    def update(self, dt: float) -> None:
        """
        Poll the network and drive the connection state: attempt/retry
        connecting, receive and dispatch messages, retransmit unacked
        reliable packets, send heartbeats, and detect a timed-out
        server.

        :param dt: Time elapsed, in seconds, since the last call. Currently unused (timing is wall-clock based), accepted for consistency with the rest of gale.
        """
        now = time.monotonic()

        if self._connecting:
            self._drive_connect(now)

        self._poll_socket(now)

        if self.connected:
            self._run_heartbeat(now)
            self._run_reliability(now)

            if now - self._last_seen > self.timeout:
                self._handle_disconnect("timed out")

    def _drive_connect(self, now: float) -> None:
        if now > self._connect_deadline:
            self._connecting = False

            for callback in self._on_connect_failed_callbacks:
                callback("timed out waiting for the server")

            return

        if now - self._last_connect_attempt >= CONNECT_RETRY_INTERVAL:
            self._last_connect_attempt = now
            body = self._serialize(CONNECT_REQUEST, {})
            header = pack_header(Channel.UNRELIABLE, 0, 0, 0, 0)
            self._socket.sendto(header + body, self._server_address)

    def _poll_socket(self, now: float) -> None:
        while True:
            try:
                data, address = self._socket.recvfrom(MAX_DATAGRAM_SIZE)
            except BlockingIOError:
                return
            except OSError:
                return

            if address != self._server_address:
                continue

            self._handle_packet(data, now)

    def _handle_packet(self, data: bytes, now: float) -> None:
        try:
            channel, token, sequence, ack, ack_bitfield = unpack_header(data)
            body = data[HEADER_SIZE:]
            message_type, payload = self._deserialize(body)
        except Exception:
            return

        if not self.connected:
            if self._connecting and message_type == CONNECT_ACCEPTED:
                self.token = token
                self.connected = True
                self._connecting = False
                self._last_seen = now

                for callback in self._on_connect_callbacks:
                    callback()

            return

        if token != self.token:
            return

        self._last_seen = now
        is_reliable = channel in (Channel.RELIABLE_ORDERED, Channel.RELIABLE_UNORDERED)

        if is_reliable:
            self._get_sender(channel).acknowledge(ack, ack_bitfield)

        if message_type == PING:
            self.send(PONG, payload, channel=Channel.UNRELIABLE)
            return

        if message_type == PONG:
            ping_id = payload.get("id")
            sent_at = self._ping_sent_at.pop(ping_id, None)

            if sent_at is not None:
                self._update_rtt(now - sent_at)

            return

        if message_type == ACK:
            return

        if is_reliable:
            receiver = self._get_receiver(
                channel, ordered=channel == Channel.RELIABLE_ORDERED
            )

            for raw in receiver.receive(sequence, body):
                try:
                    inner_type, inner_payload = self._deserialize(raw)
                except Exception:
                    continue

                self._dispatch(inner_type, inner_payload)
        else:
            self._dispatch(message_type, payload)

    def _dispatch(self, message_type: str, payload: Dict[str, Any]) -> None:
        for callback in self._on_message_callbacks.get(message_type, []):
            callback(payload)

    def _update_rtt(self, sample: float) -> None:
        if self.rtt == 0.0:
            self.rtt = sample
        else:
            self.rtt = 0.875 * self.rtt + 0.125 * sample

    def _run_heartbeat(self, now: float) -> None:
        if now - self._last_heartbeat < self.heartbeat_interval:
            return

        self._last_heartbeat = now
        ping_id = self._next_ping_id
        self._next_ping_id += 1
        self._ping_sent_at[ping_id] = now
        self.send(PING, {"id": ping_id}, channel=Channel.UNRELIABLE)

    def _run_reliability(self, now: float) -> None:
        for channel, sender in list(self._senders.items()):
            due, gave_up = sender.due_for_retransmit(now, self.rtt)

            for sequence, payload in due:
                self._send_raw(channel, sequence, payload)

            if gave_up:
                self._handle_disconnect("too many unacked reliable packets")
                return

            receiver = self._receivers.get(channel)

            if receiver is not None and receiver.highest_received is not None:
                self._send_ack_only(channel)

    def _handle_disconnect(self, reason: str) -> None:
        self.disconnect()

        for callback in self._on_disconnect_callbacks:
            callback(reason)

    def _get_sender(self, channel: int) -> ReliableSender:
        if channel not in self._senders:
            self._senders[channel] = ReliableSender()

        return self._senders[channel]

    def _get_receiver(self, channel: int, ordered: bool = False) -> ReliableReceiver:
        if channel not in self._receivers:
            self._receivers[channel] = ReliableReceiver(ordered=ordered)

        return self._receivers[channel]

    def _send_raw(self, channel: int, sequence: int, body: bytes) -> None:
        receiver = self._get_receiver(channel)
        ack, ack_bitfield = receiver.build_ack()
        header = pack_header(channel, self.token, sequence, ack, ack_bitfield)
        self._socket.sendto(header + body, self._server_address)

    def _send_ack_only(self, channel: int) -> None:
        receiver = self._get_receiver(channel)
        ack, ack_bitfield = receiver.build_ack()
        body = self._serialize(ACK, {})
        header = pack_header(channel, self.token, 0, ack, ack_bitfield)
        self._socket.sendto(header + body, self._server_address)
