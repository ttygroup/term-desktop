"services_manager.py - The uber manager to manage other managers."

# python standard library imports
from __future__ import annotations
from textual.dom import DOMNode

from textual import work

# Local imports
from term_desktop.services.servicebase import BaseService
from term_desktop.services.processmanager import ProcessManager
from term_desktop.services.apploader import AppLoader
from term_desktop.services.windowservice import WindowService


class ServicesManager(DOMNode):
    """The uber manager to manage other managers."""

    # NOTE: This is a Textual DOMNode because it will allow it to do Textual things
    # like run workers or send messages to the main app.
    # DOMNodes still cannot be mounted though, which is why this gets wrapped in the
    # ServicesWidget for attaching to the main app.

    def __init__(self) -> None:
        super().__init__()

        self.services_dict: dict[str, type[BaseService]] = {}

        self.process_manager = ProcessManager(self)
        self.services_dict["process_manager"] = ProcessManager

        self.app_loader = AppLoader(self)
        self.services_dict["app_loader"] = AppLoader

        self.window_service = WindowService(self)
        self.services_dict["window_service"] = WindowService

    async def start_all_services(self) -> None:
        """Start all services."""

        # ? This will eventually be built out to use workers and threads, with
        # a robust service management system and whatnot.
        # For now we just run them.
        self.log("ServicesManager starting all services...")

        try:
            assert isinstance(self.process_manager, BaseService)
            process_manager_success = await self.process_manager.start()
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"ProcessManager startup failed with an unexpected error: {str(e)}") from e
        else:
            if not process_manager_success:
                raise RuntimeError("ProcessManager startup returned False after running.")

        try:
            assert isinstance(self.app_loader, BaseService)
            app_loader_success = await self.app_loader.start()
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"AppLoader startup failed with an unexpected error: {str(e)}") from e
        else:
            if not app_loader_success:
                raise RuntimeError("AppLoader startup returned False after running.")

        try:
            assert isinstance(self.window_service, BaseService)
            window_service_success = await self.window_service.start()
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"WindowService startup failed with an unexpected error: {str(e)}") from e
        else:
            if not window_service_success:
                raise RuntimeError("WindowService startup returned False after running.")
