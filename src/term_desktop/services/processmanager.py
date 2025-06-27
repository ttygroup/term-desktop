"process_manager.py - The process manager for handling processes in TDE."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager
    from term_desktop.app_sdk.appbase import TDEApp

# Textual imports
from textual import log
from term_desktop.services.servicebase import BaseService

# Textual library imports
from textual_window import Window, window_manager

# Local imports
from term_desktop.app_sdk.appbase import (TDEApp, LaunchMode, DefaultWindowSettings,)


class ProcessManager(BaseService):

    def __init__(
            self, 
            services_manager: ServicesManager, 
        ) -> None:
        """        
        Initialize the process manager.

        Args:
            services_manager (ServicesManager): The services manager instance.
        """
        super().__init__(services_manager)
        self.processes: dict[str, TDEApp] = {}  #! possibly make reactive dict
        self.window_manager = window_manager


    async def start(self) -> bool:
        log("Starting ProcessManager service")
        # Nothing to do here yet.
        return True

    async def stop(self) -> bool:
        log("Stopping ProcessManager service")
        # Nothing to do here yet.
        return True
    
    async def launch_process(
            self, 
            TDE_App: type[TDEApp], 
            *args: Any,
            **kwargs: Any,
        ) -> None:
        """
        Args:
            TDEapp (TDEApp): The app to launch.
            *args: Positional arguments for the app.
            **kwargs: Keyword arguments for the app.
        """
        log(f"Launching process for app: {TDE_App.APP_NAME}")

        assert TDE_App.APP_NAME is not None # this is already validated by this point
        assert TDE_App.APP_ID is not None  



        # def get_lowest_available_number(used_numbers: set[int]) -> int:
        #     i = 1
        #     while i in used_numbers:
        #         i += 1
        #     return i

        # self.log(f"App selected: {event.app_id}")
        # registered_apps = self.app.query_one(RegisteredApps)

        # AppClass = registered_apps[event.app_id]
        # self.log(f"Mounting app with display name: {AppClass.APP_NAME}")

        # instance_counter = self.app.query_one(AppInstanceCounter)
        # try:
        #     current_set = instance_counter[event.app_id]
        # except KeyError:
        #     instance_counter[event.app_id] = set()
        #     current_set = instance_counter[event.app_id]

        # lowest_available_number = get_lowest_available_number(current_set)
        # current_set.add(lowest_available_number)

        # if lowest_available_number == 1:
        #     app_id = f"{event.app_id}"
        # else:
        #     app_id = f"{event.app_id}_{lowest_available_number}"

        # self.log.debug(f"Creating new app instance with ID: {app_id}")



        launch_mode = TDE_App.launch_mode
        if launch_mode == LaunchMode.WINDOW:

            main_content = TDE_App.main_content()
            if main_content is None:
                raise RuntimeError(
                    "The main_content method must return a Widget if your app is not a Daemon"
                )
            default_window_settings = TDE_App.default_window_settings()
            custom_window_settings = TDE_App.custom_window_settings()
            window_settings: DefaultWindowSettings = {
                **default_window_settings, **custom_window_settings
            }
            new_window = Window(
                main_content,
                id=TDE_App.APP_ID,     #! Needs instance counter
                name=TDE_App.APP_NAME,
                **window_settings
            )  

            # now mount our new window into the main screen.




        elif launch_mode == LaunchMode.FULLSCREEN:
            pass

        elif launch_mode == LaunchMode.DAEMON:
            pass

        else:
            raise ValueError(f"Recieved invalid launch mode: {launch_mode}")




        self.processes[app.APP_ID] = app




