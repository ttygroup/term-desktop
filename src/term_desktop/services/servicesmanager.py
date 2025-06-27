"services_manager.py - The uber manager to manage other managers."

# python standard library imports
from __future__ import annotations
from textual.message_pump import MessagePump

# from typing import TYPE_CHECKING, cast, Any
# from pathlib import Path

from term_desktop.services.servicebase import BaseService
from term_desktop.services.processmanager import ProcessManager
from term_desktop.services.apploader import AppLoader


class ServicesManager(MessagePump):
    """The uber manager to manage other managers."""

    def __init__(self) -> None:

        self.services_dict: dict[str, type[BaseService]] = {}

        self.process_manager: ProcessManager = ProcessManager(self)
        self.app_loader: AppLoader = AppLoader(self)

    async def start_all_services(self) -> None:
        """Start all services."""

        #? This will eventually be built out to use workers and threads, with
        # a robust service management system and whatnot.
        # For now we just run them.

        try:
            process_manager_success = await self.process_manager.start()
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"ProcessManager startup failed with an unexpected error: {str(e)}") from e
        else:
            if not process_manager_success:
                raise RuntimeError("ProcessManager startup returned False after running.")

        try:
            app_loader_success = await self.app_loader.start()
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"AppLoader startup failed with an unexpected error: {str(e)}") from e        
        else:
            if not app_loader_success:
                raise RuntimeError("AppLoader startup returned False after running.")





    # # * called by on_mount, above
    # def load_apps(self):

    #     incoming_registered_apps = self.app_loader.discover_apps()
    #     registered_apps = self.query_one(RegisteredApps)
    #     registered_apps.update(incoming_registered_apps)

    #     main_screen = self.get_screen("main", MainScreen)  # type: ignore ( BUG IN TEXTUAL )
    #     main_screen.query_one(StartMenu).load_registered_apps(registered_apps)