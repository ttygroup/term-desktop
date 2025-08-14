"mainscreen.py"

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING  # , cast

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from term_desktop.aceofbase import ProcessContext

# # Textual imports
from textual.widgets import Static
from textual.binding import Binding
from textual import getters

# from textual import on, events  # , work

# # Textual library imports
# from textual_window import Window, WindowSwitcher
# from textual_slidecontainer import SlideContainer

# Local imports
from term_desktop.screens.screenbase import TDEScreenBase, TDEScreen
from term_desktop.shell.shellmanager import ShellManager
from term_desktop.common import (
    DummyScreen,
)


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

    shell_manager = getters.child_by_id("shell_manager", ShellManager)

    BINDINGS = [
        Binding("f4", "toggle_windowswitcher", "Toggle Window Switcher"),
        Binding("f2", "toggle_explorer", "Toggle File Explorer"),
        Binding("f1", "toggle_startmenu", "Toggle Start Menu"),
        Binding("f5", "toggle_windowbar", "Toggle Task Bar"),
        Binding("f12", "toggle_transparency", "Toggle Transparency"),
    ]

    def __init__(self, process_context: ProcessContext) -> None:
        super().__init__(process_context)
        self.styles.opacity = 0.0  # Start with the screen hidden
        self.call_after_refresh(self.screen_ready)

    def compose(self) -> ComposeResult:

        try:
            yield ShellManager(self.services, id="shell_manager")
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

    ###############
    # ~ Actions ~ #
    ###############

    def action_toggle_transparency(self) -> None:
        self.app.ansi_color = not self.app.ansi_color
        self.app.push_screen(DummyScreen())

    # @on(ToggleTaskBar)
    def action_toggle_windowbar(self) -> None:
        """Toggle the visibility of the window bar."""
        self.shell_manager.action_toggle_windowbar()

    # @on(ToggleWindowSwitcher)
    def action_toggle_windowswitcher(self) -> None:
        """Toggle the visibility of the window switcher."""
        self.shell_manager.action_toggle_windowswitcher()

    # @on(ToggleExplorer)
    def action_toggle_explorer(self) -> None:
        """Toggle the visibility of Slide Menu 1."""
        self.shell_manager.action_toggle_explorer()

    # @on(ToggleStartMenu)
    def action_toggle_startmenu(self) -> None:
        """Open the start menu / quick launcher."""
        self.shell_manager.action_toggle_startmenu()
