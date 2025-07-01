"term-desktop"

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING  # , cast

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.widgets.directory_tree import DirEntry

# # Textual imports
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
from term_desktop.screens.screenbase import ScreenBase
from term_desktop.core.shell import Shell


class MainScreen(ScreenBase):
    """
    The main screen of the Terminal Desktop Environment.
    This screen is responsible for displaying the main content area,
    which includes the shell and other widgets.
    """

    def __init__(self, id: str) -> None:
        super().__init__(id)
        self.shell = Shell()

    def build(self) -> ComposeResult:
        """
        Build the main screen with the shell widget.
        """
        return self.shell.build()
