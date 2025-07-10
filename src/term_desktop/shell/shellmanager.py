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

    def __init__(self, services: ServicesManager) -> None:
        super().__init__()
        self.services = services
        self.services.shell_service.register_mounting_callback(self.mounting_callback)
        self.registered_shells = self.services.shell_service.registered_shells        
        self.load_registered_shells(self.registered_shells)
        
    def on_mount(self) -> None:
        self.load_chosen_shell()

    async def mounting_callback(self, shell: TDEShellSession) -> None:
        await self.mount(shell)

    def load_registered_shells(self, registered_shells: dict[str, type[TDEShellBase]]) -> None:

        registred_shells_str = ""
        for key, value in registered_shells.items():
            registred_shells_str += f"{key} -> {value.SHELL_NAME}\n"
        self.log.info(f"Registered shells in Shell Manager:\n{registred_shells_str}")

    def load_chosen_shell(self) -> None:
        # There is no chosen shell at the moment. Only the default shell is available.
        self.log.info("No chosen shell. Using the default shell.")
        self.services.shell_service.mount_default_shell()

