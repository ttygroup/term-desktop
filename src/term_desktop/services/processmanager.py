"process_manager.py - The process manager for handling processes in TDE."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING  # , Any

if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager
    from term_desktop.app_sdk.appbase import TDEApp, DefaultWindowSettings, CustomWindowMounts
    from textual.widget import Widget

# Textual imports
from textual import log

# Textual library imports
# from textual_window import Window

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

        #! Make these reactive dicts
        self._processes: dict[str, TDEApp] = {}
        self._instance_counter: dict[str, set[int]] = {}
        self._content_instance_dict: dict[str, list[Widget]] = {}
        self._custom_mounts_dict: dict[str, CustomWindowMounts] = {}

        # NOTE: Storing all the content instances and custom mounts in dictionaries
        # will make it easier for the process manager to do stuff like restart processes
        # on its own in the future. Right now it is just scaffolding.

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
            current_set = self._instance_counter[TDE_App.APP_ID]  # get set if exists
        except KeyError:
            current_set: set[int] = set()  # if not, make a new set
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

        assert TDE_App.APP_NAME is not None  # this is already validated by this point
        assert TDE_App.APP_ID is not None

        # Get the app ID with a number if needed
        # This is to handle multiple instances of the same app.
        app_id = self._get_app_id_with_num(TDE_App)

        # * Create the app process instance
        # This is the instance of the base app inherited from the TDEApp class. Right now
        # it just holds all the app metadata. Store this in the process manager.
        app_process = TDE_App(id=app_id)
        self._add_process_to_dict(app_process, app_id)

        # The rest is pretty self explanatory.
        launch_mode = app_process.launch_mode()
        if launch_mode == LaunchMode.WINDOW:

            main_content = app_process.get_main_content()
            if main_content is None:
                log.error("The main_content property must return a Widget if your app is not a Daemon")
                #! Create error popup for user here
                return
            try:
                content_instance = main_content()
            except Exception as e:
                log.error(f"Failed to create main content instance for {app_process.APP_NAME}: {e}")
                #! Create error popup for user here
                return

            # Store any content instances in the dictionary for keeping track of them.
            # Right now this whole system is only designed for one content instance, but
            # in the future we might want to support multiple content instances per app.
            self._content_instance_dict[app_id] = [content_instance]

            # Merge the default window settings with any custom settings
            # Custom settings will override the default settings.
            default_window_settings = app_process.default_window_settings
            custom_window_settings = app_process.custom_window_settings()
            window_settings: DefaultWindowSettings = {**default_window_settings, **custom_window_settings}

            # The custom window mounts should be a static set of decorative or utility
            # widgets. Only one set of custom mounts is supported per app. Every time
            # an app is launched, it will override the previous custom mounts.
            custom_window_mounts = app_process.custom_window_mounts()
            self._custom_mounts_dict[app_id] = custom_window_mounts

            self.services_manager.window_service.create_new_window(
                content_instance=content_instance,
                app_id=app_id,
                window_dict=window_settings,
                custom_mounts=custom_window_mounts,
                callback_id="main_desktop",
            )

        elif launch_mode == LaunchMode.FULLSCREEN:
            pass  # coming soon

        elif launch_mode == LaunchMode.DAEMON:
            pass

        else:
            log.error(f"Unknown launch mode {launch_mode} for app {app_process.APP_NAME}")
            #! Create error popup for user here
            return
