"mainscreen.py"

#! NOT A TEMPLATE
#! FINISH ME

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING  # , cast

if TYPE_CHECKING:
    from textual.app import ComposeResult

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

    def compose(self) -> ComposeResult:

        try:
            yield ShellManager(self.services)
        except Exception as e:
            yield Static(f"Error mounting shell: {e}", classes="error")

    # def on_mount(self) -> None:
    #     self.call_after_refresh(self.mount_shell)

    # async def mount_shell(self) -> None:
    #     await self.mount(ShellManager(self.services))
