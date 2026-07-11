import pygame

from gale.input_handler import InputData
from gale.net.client import Client
from gale.net.discovery import discover_lan_servers
from gale.net.server import Server
from gale.state import BaseState
from gale.ui.button import Button
from gale.ui.container import Container
from gale.ui.label import Label
from gale.ui.manager import UIManager
from gale.ui.panel import Panel
from gale.ui.text_input import TextInput

import settings


class LobbyState(BaseState):
    """
    Waits for the other racer to show up: as host, listens for one
    connection and advertises itself on the LAN (and starts racing the
    AI alone in the meantime, since a solo practice lap is still a
    complete race); as a joining player, lets you type a "host:port" or
    scan the LAN for one and connect, joining the race already under
    way.
    """

    def enter(self, is_host: bool) -> None:
        self.is_host = is_host
        self.server = None
        self.client = None

        if is_host:
            self._enter_as_host()
        else:
            self._enter_as_joiner()

    def _enter_as_host(self) -> None:
        self.server = Server(port=settings.DEFAULT_PORT, max_peers=1)
        self.server.enable_lan_discovery(
            "Circuit Race", discovery_port=settings.DEFAULT_DISCOVERY_PORT
        )
        self.state_machine.change("play", is_host=True, server=self.server, client=None)

    def _enter_as_joiner(self) -> None:
        self.client = Client()
        self.client.on_connect(self._on_connected)
        self.client.on_connect_failed(self._on_connect_failed)

        center_x = settings.VIRTUAL_WIDTH / 2
        self.address_input = TextInput(
            center_x - 100,
            settings.VIRTUAL_HEIGHT / 2 - 40,
            200,
            28,
            initial_text=f"127.0.0.1:{settings.DEFAULT_PORT}",
        )
        self.status_label = Label(
            center_x,
            settings.VIRTUAL_HEIGHT / 2 + 60,
            "",
            font=settings.FONTS["small"],
            center=True,
        )
        root = Container(
            0,
            0,
            settings.VIRTUAL_WIDTH,
            settings.VIRTUAL_HEIGHT,
            children=[
                Panel(center_x - 110, settings.VIRTUAL_HEIGHT / 2 - 60, 220, 140),
                self.address_input,
                Button(
                    center_x - 100,
                    settings.VIRTUAL_HEIGHT / 2,
                    95,
                    28,
                    "Connect",
                    on_click=self._connect,
                ),
                Button(
                    center_x + 5,
                    settings.VIRTUAL_HEIGHT / 2,
                    95,
                    28,
                    "Scan LAN",
                    on_click=self._scan,
                ),
                self.status_label,
                Button(
                    center_x - 60,
                    settings.VIRTUAL_HEIGHT / 2 + 30,
                    120,
                    28,
                    "Back",
                    on_click=self._back,
                ),
            ],
        )
        self.ui = UIManager(
            root,
            virtual_width=settings.VIRTUAL_WIDTH,
            window_width=settings.WINDOW_WIDTH,
            virtual_height=settings.VIRTUAL_HEIGHT,
            window_height=settings.WINDOW_HEIGHT,
            confirm_action="confirm",
            navigate_actions={"throttle_up": (0, -1), "throttle_down": (0, 1)},
        )

    def _connect(self) -> None:
        host, _, port_str = self.address_input.text.partition(":")
        port = int(port_str) if port_str.isdigit() else settings.DEFAULT_PORT

        if not host:
            self.status_label.set_text("Enter a host to connect to.")
            return

        self.status_label.set_text(f"Connecting to {host}:{port}...")
        self.client.connect(host, port)

    def _scan(self) -> None:
        found = discover_lan_servers(
            discovery_port=settings.DEFAULT_DISCOVERY_PORT, timeout=0.5
        )

        if found:
            server_info = found[0]
            self.address_input.text = (
                f"{server_info.address[0]}:{server_info.address[1]}"
            )
            self.address_input.cursor_index = len(self.address_input.text)
            self.status_label.set_text(f"Found {server_info.name!r}. Press Connect.")
        else:
            self.status_label.set_text("No servers found on the LAN.")

    def _on_connected(self) -> None:
        self.state_machine.change(
            "play", is_host=False, server=None, client=self.client
        )

    def _on_connect_failed(self, reason: str) -> None:
        self.status_label.set_text(f"Connect failed: {reason}")

    def _back(self) -> None:
        if self.client is not None:
            self.client.close()

        if self.server is not None:
            self.server.close()

        self.state_machine.change("title")

    def update(self, dt: float) -> None:
        if self.client is not None:
            self.client.update(dt)

        if hasattr(self, "ui"):
            self.ui.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)

        if hasattr(self, "ui"):
            self.ui.render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if hasattr(self, "ui"):
            self.ui.on_input(input_id, input_data)
