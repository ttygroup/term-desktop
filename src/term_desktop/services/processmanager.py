"process_manager.py - The process manager for handling processes in TDE."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING #, Any
if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager
    from term_desktop.app_sdk.appbase import TDEApp, DefaultWindowSettings

# Textual imports
from textual import log

# Textual library imports
from textual_window import Window

# Local imports
from term_desktop.services.servicebase import BaseService
from term_desktop.app_sdk.appbase import LaunchMode


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

        self._processes: dict[str, TDEApp] = {}  #! Make reactive dict
        self._instance_counter: dict[str, set[int]] = {}

    async def start(self) -> bool:
        log("Starting ProcessManager service")
        # Nothing to do here yet.
        return True

    async def stop(self) -> bool:
        log("Stopping ProcessManager service")
        self._processes.clear()
        self._instance_counter.clear()
        return True

    @property
    def processes(self) -> dict[str, TDEApp]:
        """Get the currently running processes."""
        return self._processes

    @property
    def instance_counter(self) -> dict[str, set[int]]:
        """Get the instance counter for each app ID."""
        return self._instance_counter
    
    def _add_process_to_dict(self, tde_app_instance: TDEApp, app_id: str) -> None:
        """Add a process to the manager."""

        if app_id in self._processes:
            raise RuntimeError(f"Process with ID {app_id} already exists.")
        
        self._processes[app_id] = tde_app_instance
        log(f"Process {tde_app_instance.APP_NAME} with ID {app_id} added.")
    

    def _get_app_id_with_num(self, TDE_App: type[TDEApp]) -> str:

        assert TDE_App.APP_ID is not None and TDE_App.APP_NAME is not None
        try:
            current_set = self._instance_counter[TDE_App.APP_ID] # get set if exists
        except KeyError:
            current_set: set[int] = set()       # if not, make a new set
            self._instance_counter[TDE_App.APP_ID] = current_set

        i = 1
        while i in current_set:
            i += 1
        current_set.add(i)
        if i == 1:
            return f"{TDE_App.APP_ID}"
        else:
            return f"{TDE_App.APP_ID}_{i}"        

    #! TODO: make this a worker once confirmed working
    async def launch_process(self, TDE_App: type[TDEApp]) -> None:
        """
        Args:
            TDEapp (TDEApp): The app to launch.
        """
        log(f"Launching process for app: {TDE_App.APP_NAME}")

        assert TDE_App.APP_NAME is not None # this is already validated by this point
        assert TDE_App.APP_ID is not None

        app_id = self._get_app_id_with_num(TDE_App) 
        app_process = TDE_App(id=app_id)
        self._add_process_to_dict(app_process, app_id)
        launch_mode = app_process.get_launch_mode()

        if launch_mode == LaunchMode.WINDOW:

            main_content = app_process.get_main_content()
            if main_content is None:
                log.error(
                    "The main_content property must return a Widget if your app is not a Daemon"
                )
                #! Create error popup for user here
                return
            default_window_settings = app_process.default_window_settings
            custom_window_settings = app_process.get_custom_window_settings()
            window_settings: DefaultWindowSettings = {
                **default_window_settings, **custom_window_settings
            } 

            try:
                content_instance = main_content()
            except Exception as e:
                log.error(f"Failed to create main content instance for {app_process.APP_NAME}: {e}")
                #! Create error popup for user here
                return

            self.services_manager.window_service.mount_window(
                Window(
                    content_instance,
                    id=app_id, 
                    name=app_process.APP_NAME,
                    **window_settings
                ), 
                callback_id="main_desktop"
            )

        elif launch_mode == LaunchMode.FULLSCREEN:
            pass    # coming soon

        elif launch_mode == LaunchMode.DAEMON:
            pass

        else:
            log.error(f"Unknown launch mode {launch_mode} for app {app_process.APP_NAME}")
            #! Create error popup for user here
            return




