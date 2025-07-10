"mainscreen.py"

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING  # , cast

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from term_desktop.aceofbase import ProcessContext

# # Textual imports
from textual.widgets import Static

# from textual import on, events  # , work
# from textual.widgets import (
#     DirectoryTree,
# )
# from textual.binding import Binding
# from textual.screen import Screen

# # Textual library imports
# from textual_window import Window, WindowSwitcher
# from textual_slidecontainer import SlideContainer

# Local imports
from term_desktop.screens.screenbase import TDEScreenBase, TDEScreen
from term_desktop.shell.shellmanager import ShellManager

class MainScreenMeta(TDEScreenBase):
    """
    The main screen of the Terminal Desktop Environment.
    This screen is responsible for displaying the main content area,
    which includes the shell and other widgets.
    """

    SCREEN_ID = "main_screen"

    def get_screen(self) -> type[TDEScreen]:
        return MainScreen


class MainScreen(TDEScreen):

    def __init__(self, process_context: ProcessContext) -> None:
        super().__init__(process_context)
        self.styles.opacity = 0.0  # Start with the screen hidden
        self.call_after_refresh(self.screen_ready)

    def compose(self) -> ComposeResult:

        try:
            yield ShellManager(self.services)
        except Exception as e:
            yield Static(f"Error mounting shell: {e}", classes="error")

    async def screen_ready(self) -> None:

        def animate_ready() -> None:
            self.styles.animate(
                "opacity",
                1.0,
                duration=0.3,
            )
        self.set_timer(0.3, animate_ready)
