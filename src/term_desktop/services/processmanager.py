"process_manager.py - The process manager for handling processes in TDE."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING, TypedDict  # , Any
if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager
    from term_desktop.app_sdk.appbase import (
        TDEApp,
        DefaultWindowSettings,
        TDEMainWidget,
    )

# Textual imports
from textual import log

# Textual library imports
# from textual_window import Window

# Local imports
from term_desktop.services.servicebase import BaseService
from term_desktop.app_sdk import LaunchMode


class AppContext(TypedDict, total=True):
    """Context for the app, passed to the main content widget. \n

    This is used to provide access to the services manager and other context-specific
    information that the app might need.
    """

    process_id: str  # The ID of the process running the app.
    services: ServicesManager  # The services manager instance
    # Add more context-specific fields as needed.


class ProcessManager(BaseService):

    #####################
    # ~ Initialzation ~ #
    #####################

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
        self._content_instance_dict: dict[str, TDEMainWidget] = {}

        # NOTE: Storing all the content instances and custom mounts in dictionaries
        # will make it easier for the process manager to do stuff like restart processes
        # on its own in the future. Right now it is just scaffolding.

    ####################
    # ~ External API ~ #
    ####################
    # This section is for methods or properties that might need to be
    # accessed by anything else in TDE, including other services.

    @property
    def processes(self) -> dict[str, TDEApp]:
        """Get the currently running processes."""
        return self._processes

    @property
    def instance_counter(self) -> dict[str, set[int]]:
        """Get the instance counter for each app ID."""
        return self._instance_counter

    @property
    def content_instance_dict(self) -> dict[str, TDEMainWidget]:
        """Get the dictionary of main content widgets for each app ID"""
        return self._content_instance_dict

    async def start(self) -> bool:
        log("Starting ProcessManager service")
        # Nothing to do here yet.
        return True

    async def stop(self) -> bool:
        log("Stopping ProcessManager service")
        self._processes.clear()
        self._instance_counter.clear()
        return True

    async def request_process_launch(
        self,
        TDE_App: type[TDEApp],
    ) -> None:
        """
        Request the process manager to launch a new process for the given TDEApp.

        Args:
            TDE_App (type[TDEApp]): The app class to launch.
        """
        log(f"Requesting process launch for app: {TDE_App.APP_NAME}")

        # Launch the process asynchronously
        # TODO: this should be sync function + worker call
        await self._launch_process(TDE_App)

    def get_process_by_id(self, process_id: str) -> TDEApp:
        """
        Get a process by its ID.

        Args:
            process_id (str): The ID of the process to retrieve.

        Returns:
            TDEApp: The app instance associated with the given process ID.
        """
        if process_id not in self._processes:
            raise KeyError(f"Process with ID {process_id} does not exist.")
        return self._processes[process_id]

    ################
    # ~ Internal ~ #
    ################
    # This section is for methods that are only used internally 
    # These should be marked with a leading underscore.

    def _add_process_to_dict(self, tde_app_instance: TDEApp, process_id: str) -> None:
        """Add a process to the manager."""

        if process_id in self._processes:
            raise RuntimeError(f"Process with ID {process_id} already exists.")

        self._processes[process_id] = tde_app_instance
        log(f"Process {tde_app_instance.APP_NAME} with ID {process_id} added.")

    def _set_available_process_id(self, APP_ID: str) -> str:

        try:
            current_set = self._instance_counter[APP_ID]  # get set if exists
        except KeyError:
            current_set: set[int] = set()  # if not, make a new set
            self._instance_counter[APP_ID] = current_set

        i = 1
        while i in current_set:
            i += 1
        current_set.add(i)
        if i == 1:
            return f"{APP_ID}"
        else:
            return f"{APP_ID}_{i}"

    #! TODO: make this a worker once we have the MetaABC set up
    async def _launch_process(self, TDE_App: type[TDEApp]) -> None:
        """
        Args:
            TDEapp (TDEApp): The app to launch.
        """
        log(f"Launching process for app: {TDE_App.APP_NAME}")

        assert TDE_App.APP_NAME is not None  # this is already validated by this point
        assert TDE_App.APP_ID is not None

        # Get the app ID with a number if needed
        # This is to handle multiple instances of the same app.
        process_id = self._set_available_process_id(TDE_App.APP_ID)

        # * Create the app process instance
        # This is the instance of the base app inherited from the TDEApp class. Right now
        # it just holds all the app metadata. Store this in the process manager.
        app_process = TDE_App(id=process_id)
        self._add_process_to_dict(app_process, process_id)

        app_context: AppContext = {
            "process_id": process_id,
            "services": self.services_manager,
        }

        # The rest is pretty self explanatory.
        launch_mode = app_process.launch_mode()
        if launch_mode == LaunchMode.WINDOW:

            main_content = app_process.get_main_content()
            if main_content is None:
                log.error("The main_content property must return a Widget if your app is not a Daemon")
                #! Create error popup for user here
                return
            try:
                content_instance = main_content(app_context)
            except Exception as e:
                log.error(f"Failed to create main content instance for {app_process.APP_NAME}: {e}")
                #! Create error popup for user here
                return

            # Store the main content instance in the dictionary so that it can
            # be tracked or queried
            self._content_instance_dict[process_id] = content_instance

            # Merge the default window settings with any custom settings
            # Custom settings will override the default settings
            default_window_settings = app_process.default_window_settings
            custom_window_settings = app_process.custom_window_settings()
            window_settings: DefaultWindowSettings = {**default_window_settings, **custom_window_settings}

            # The custom window mounts should be a static set of decorative or utility
            # widgets. The window mounts and the window styles will be loaded from the
            # app process instance every time a new process is launched
            custom_window_mounts = app_process.custom_window_mounts()
            window_styles = app_process.window_styles()

            await self.services_manager.window_service.create_new_window(
                content_instance=content_instance,
                process_id=process_id,
                window_dict=window_settings,
                custom_mounts=custom_window_mounts,
                styles_dict=window_styles,
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
