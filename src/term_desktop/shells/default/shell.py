"mainscreen.py"

# python standard library imports
from __future__ import annotations

# from typing import TYPE_CHECKING  # , cast

# if TYPE_CHECKING:
# from textual.app import ComposeResult

# # Textual imports
# from textual.widgets import Static

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
from term_desktop.shell.shellbase import TDEShellBase, TDEShellSession


class DefaultShell(TDEShellBase):
    """
    The default shell of the Terminal Desktop Environment.
    """

    SHELL_ID = "default_shell"
    SHELL_NAME = "Default Shell"
    ICON = "🧱"
    DESCRIPTION = "The default shell for the Terminal Desktop Environment."
    SHELL_AUTHOR = "TDE Team"

    def get_shell_session(self) -> type[TDEShellSession]:
        return DefaultShellSession


class DefaultShellSession(TDEShellSession):
    """
    The default shell session for the Terminal Desktop Environment.
    This session is responsible for handling the shell's functionality.
    """

    # ~ Thats all she wrote bubs!
