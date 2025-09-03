"shellmanager.py"

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING  # , cast

if TYPE_CHECKING:
    # from textual.app import ComposeResult
    from term_desktop.services import ServicesManager
    from term_desktop.shell.shellbase import TDEShellBase, TDEShellSession

# Textual imports
# from textual import on, events  # , work
# from textual.binding import Binding
from textual.widget import Widget


#################
# Local imports #
#################
# None right now


class ShellManager(Widget):

    def __init__(self, services: ServicesManager, id: str) -> None:
        super().__init__(id=id)
        self._services = services
        self.services.shell_service.register_mounting_callback(self.mounting_callback)
        self.registered_shells = self.services.shell_service.registered_shells
        self.current_shell: TDEShellSession | None = None
        self.load_registered_shells(self.registered_shells)

    @property
    def services(self) -> ServicesManager:
        return self._services

    def on_mount(self) -> None:
        self.load_chosen_shell()

    async def mounting_callback(self, shell: TDEShellSession) -> None:
        await self.mount(shell)
        self.current_shell = shell

    def load_registered_shells(self, registered_shells: dict[str, type[TDEShellBase]]) -> None:

        registred_shells_str = ""
        for key, value in registered_shells.items():
            registred_shells_str += f"{key} -> {value.SHELL_NAME}\n"
        self.log.info(f"Registered shells in Shell Manager:\n{registred_shells_str}")

    def load_chosen_shell(self) -> None:
        # There is no chosen shell at the moment. Only the default shell is available.
        self.log.info("No chosen shell. Using the default shell.")
        self.services.shell_service.mount_default_shell()

    ###############
    # ~ Actions ~ #
    ###############

    # @on(ToggleTaskBar)
    def action_toggle_windowbar(self) -> None:
        """Toggle the visibility of the window bar."""
        if self.current_shell is not None:
            self.current_shell.action_toggle_windowbar()

    # @on(ToggleWindowSwitcher)
    def action_toggle_windowswitcher(self) -> None:
        """Toggle the visibility of the window switcher."""
        if self.current_shell is not None:
            self.current_shell.action_toggle_windowswitcher()

    # @on(ToggleExplorer)
    def action_toggle_explorer(self) -> None:
        """Toggle the visibility of Slide Menu 1."""
        if self.current_shell is not None:
            self.current_shell.action_toggle_explorer()

    # @on(ToggleStartMenu)
    def action_toggle_startmenu(self) -> None:
        """Open the start menu / quick launcher."""
        if self.current_shell is not None:
            self.current_shell.action_toggle_startmenu()

    def action_toggle_bg_animation(self) -> None:
        """Toggle the background animation."""
        if self.current_shell is not None:
            self.current_shell.action_toggle_bg_animation()