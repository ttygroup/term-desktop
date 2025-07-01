"services_manager.py - The uber manager to manage other managers."

# python standard library imports
from __future__ import annotations
from textual.widget import Widget

from textual import work
from textual.message import Message

# Local imports
from term_desktop.services.servicebase import TDEServiceBase
from term_desktop.services.apps import AppService
from term_desktop.services.apploader import AppLoader
from term_desktop.services.windows import WindowService
from term_desktop.services.screens import ScreenService
from term_desktop.services.shells import ShellService


class ServicesManager(Widget):
    """The uber manager to manage other managers."""

    # NOTE: This is a Textual Widget because it will allow it to do Textual things
    # like run workers or send messages to the main app.

    class ServicesStarted(Message):
        """Message to indicate that all services have been started."""

        def __init__(self) -> None:
            super().__init__()

    def __init__(self) -> None:
        super().__init__()
        self.display = False

        self.services_dict: dict[str, type[TDEServiceBase]] = {}

        self.app_service = AppService(self)
        self.services_dict["app_service"] = AppService

        self.app_loader = AppLoader(self)
        self.services_dict["app_loader"] = AppLoader

        self.window_service = WindowService(self)
        self.services_dict["window_service"] = WindowService

        self.screen_service = ScreenService(self)
        self.services_dict["screen_service"] = ScreenService

        self.shell_service = ShellService(self)
        self.services_dict["shell_service"] = ShellService

    @work(exclusive=True, group="service_manager")
    async def start_all_services(self) -> None:
        """Start all services."""

        # ? This will eventually be built out to have some kind of monitoring
        # system to watch the state of active services, stop/restart them, etc.
        self.log("ServicesManager starting all services...")

        try:
            assert isinstance(self.app_service, TDEServiceBase)
            app_service_success = await self.app_service.start()
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"AppService startup failed with an unexpected error: {str(e)}") from e
        else:
            if not app_service_success:
                raise RuntimeError("AppService startup returned False after running.")

        try:
            assert isinstance(self.app_loader, TDEServiceBase)
            app_loader_success = await self.app_loader.start()
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"AppLoader startup failed with an unexpected error: {str(e)}") from e
        else:
            if not app_loader_success:
                raise RuntimeError("AppLoader startup returned False after running.")

        try:
            assert isinstance(self.window_service, TDEServiceBase)
            window_service_success = await self.window_service.start()
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"WindowService startup failed with an unexpected error: {str(e)}") from e
        else:
            if not window_service_success:
                raise RuntimeError("WindowService startup returned False after running.")

        try:
            assert isinstance(self.screen_service, TDEServiceBase)
            screen_service_success = await self.screen_service.start()
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"ScreenService startup failed with an unexpected error: {str(e)}") from e
        else:
            if not screen_service_success:
                raise RuntimeError("ScreenService startup returned False after running.")

        try:
            assert isinstance(self.shell_service, TDEServiceBase)
            shell_service_success = await self.shell_service.start()
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"ShellService startup failed with an unexpected error: {str(e)}") from e
        else:
            if not shell_service_success:
                raise RuntimeError("ShellService startup returned False after running.")

        self.post_message(self.ServicesStarted())
