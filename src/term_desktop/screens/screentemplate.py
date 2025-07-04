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


class ShellSession(AceOfBase):

    @abstractmethod
    def get_layout(self) -> ShellManager:
        """Returns the main shell layout widget to mount on screen."""

    @abstractmethod
    def session_id(self) -> str:
        """Returns a unique identifier for this shell session."""

    def on_enter(self) -> None:
        """Called when this shell session becomes active."""

    def on_exit(self) -> None:
        """Called before this session is replaced or terminated."""


class TDEShellSession:
    """
    Terminal Desktop Environment Shell Session.
    This class implements the ShellSession interface for the TDE.
    It provides methods to get the shell layout and session ID.
    """

    def get_layout(self) -> ShellManager:
        """Returns the main shell layout widget to mount on screen."""
        return ShellManager()

    def session_id(self) -> str:
        """Returns a unique identifier for this shell session."""
        return "tde_shell_session"
