"process_manager.py - The process manager for handling processes in TDE."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING #, Any
if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager
    from textual.screen import Screen
    # from term_desktop.app_sdk.appbase import TDEApp

# Textual imports
# from textual import log
from term_desktop.services.servicebase import BaseService

# Textual library imports
from textual_window import window_manager

# Local imports
# from term_desktop.app_sdk.appbase import TDEApp


class WindowManager(BaseService):

    def __init__(
        self, 
        services_manager: ServicesManager, 
    ) -> None:
        """        
        Initialize the [INSERT SERVICE NAME HERE]
        """
        super().__init__(services_manager)
        self.window_manager = window_manager
        self.main_screen: Screen[None] | None = None
        

    async def start(self) -> bool:
        return True

    async def stop(self) -> bool:
        return True
