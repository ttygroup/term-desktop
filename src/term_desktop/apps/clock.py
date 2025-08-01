"""clock.py"""

# Python imports
from __future__ import annotations
from datetime import datetime

# Textual imports
from textual.app import ComposeResult
from textual.widgets import Digits

# Textual library imports
from textual_window.window import WindowStylesDict

# Local imports
from term_desktop.app_sdk import (
    TDEAppBase,
    TDEMainWidget,
    LaunchMode,
    CustomWindowSettings,
)


class ClockMeta(TDEAppBase):

    APP_NAME: str | None = "Clock"
    APP_ID: str | None = "clock"
    ICON: str = "🕒"
    DESCRIPTION: str = "Simple digital clock"
    APP_AUTHOR = "TDE Team"

    def launch_mode(self) -> LaunchMode:

        return LaunchMode.WINDOW  # or FULLSCREEN, or DAEMON

    def get_main_content(self) -> type[TDEMainWidget] | None:

        return ClockWidget

    def custom_window_settings(self) -> CustomWindowSettings:

        return {
            "allow_resize": False,
            "allow_maximize": False,
        }

    def window_styles(self) -> WindowStylesDict:

        return {
            "width": 28,
            "height": 7,
        }


class ClockWidget(TDEMainWidget):

    DEFAULT_CSS = """
    Window.clock {
        ClockWidget {
            align: center middle;
        }

        Digits {
            width: auto;
        }
    }
    """

    def compose(self) -> ComposeResult:
        yield Digits("")

    def on_mount(self) -> None:
        self.update_clock()
        self.set_interval(1, self.update_clock)

    def update_clock(self) -> None:
        clock = datetime.now().time()
        self.query_one(Digits).update(f"{clock:%T}")
