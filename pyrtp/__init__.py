"""Python Remote Touchpad.
    Version: v1.0.0."""

from flask import Flask

from flask_socketio import SocketIO

from logging import getLogger, CRITICAL

from socket import gethostbyname, gethostname

from threading import Thread

from typing import Callable, NoReturn


class PyRTP:
    """Remote touchpad."""

    VERSION: str = 'v1.0.0'

    def __init__(self, name: str, port: int=9876) -> None:
        """Create local touchpad."""
        self.flask_app = Flask(name); getLogger('werkzeug').setLevel(CRITICAL)

        self.socket_io = SocketIO(self.flask_app)

        self.port = port

        self.connected = True

        self.device_size = None

        self.device_orientation = None

        self.touching = False

        with open('pyrtp/client_index.html', 'r') as client_index_:
            index_page = client_index_.read()

        self.flask_app.add_url_rule('/', None, lambda: index_page.replace('%Version%', PyRTP.VERSION))

        @self.socket_io.on('connected')
        def _(_): self.connected = True

        @self.socket_io.on('set_screen_size')
        def _(size): self.device_size = size

        @self.socket_io.on('set_orientation')
        def _(orientation): self.device_orientation = 'portrait' if 'portrait' in orientation else 'landscape'

        @self.socket_io.on('touched')
        def _(touched): self.touching = touched

    def is_connected(self) -> bool:
        """Is connected."""
        return self.connected

    def get_device_size(self) -> tuple[int, int]:
        """Get device size."""
        return self.device_size

    def get_device_orientation(self) -> str:
        """Get device orientation."""
        return self.device_orientation

    def is_touching(self) -> bool:
        """Is touching."""
        return self.touching

    def set_on_touch_start(self, handler: Callable[[tuple[int, int, int]], NoReturn]) -> None:
        """Set on screen touch handler."""
        @self.socket_io.on('touch_start')
        def _(position) -> NoReturn: handler(tuple(position))

    def set_on_touch_end(self, handler: Callable[[int], NoReturn]) -> None:
        """Set on screen touch end handler."""
        @self.socket_io.on('touch_end')
        def _(touch) -> NoReturn: handler(touch)
    
    def set_on_touch_move(self, handler: Callable[[tuple[int, int, int]], NoReturn]) -> None:
        """Set on screen touch move handler."""
        @self.socket_io.on('touch_move')
        def _(position) -> NoReturn: handler(tuple(position))

    def set_touch(self, touch_position: int) -> None:
        """Set touch."""
        self.socket_io.emit('set_touch', touch_position)

    def cast_position(self, position: tuple[int, int], map_: tuple[int, int]) -> tuple[int, int]:
        """Create linear mapping for coordinates."""
        if self.device_size:
            return ((position[0] / self.device_size[0]) * map_[0], (position[1] / self.device_size[1]) * map_[1])

        else:
            return (-1, -1)

    def run(self, threaded: bool=False, log_address: bool=True) -> None:
        """Run server."""
        if log_address:
            print(f'Touchpad Address -> http://{gethostbyname(gethostname())}:{self.port}')

        execute = lambda: self.socket_io.run(self.flask_app, gethostbyname(gethostname()), port=self.port, debug=False, log_output=False)

        if threaded:
            Thread(target=execute).start()

        else:
            execute()
