"processes.py - The process service for handling processes in TDE."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from term_desktop.services.manager import ServicesManager
    from term_desktop.app_sdk.appbase import (
        TDEAppBase,
        DefaultWindowSettings,
        TDEMainWidget,
    )

# Local imports
from term_desktop.services.servicebase import TDEServiceBase
from term_desktop.app_sdk import LaunchMode
from term_desktop.aceofbase import ProcessContext, ProcessType


class AppService(TDEServiceBase):

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
        self._processes: dict[str, TDEAppBase] = {}
        self._instance_counter: dict[str, set[int]] = {}
        self._content_instance_dict: dict[str, TDEMainWidget] = {}

        # NOTE: Storing all the content instances and custom mounts in dictionaries
        # will make it easier for the process manager to do stuff like restart processes
        # on its own in the future. Right now it is just scaffolding.

    ################
    # ~ Messages ~ #
    ################
    # None yet

    ####################
    # ~ External API ~ #
    ####################
    # This section is for methods or properties that might need to be
    # accessed by anything else in TDE, including other services.

    @property
    def processes(self) -> dict[str, TDEAppBase]:
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
        self.log("Starting ProcessManager service")
        # Nothing to do here yet.
        return True

    async def stop(self) -> bool:
        self.log("Stopping ProcessManager service")
        self._processes.clear()
        self._instance_counter.clear()
        return True

    async def request_process_launch(
        self,
        TDE_App: type[TDEAppBase],
    ) -> None:
        """
        Request the process manager to launch a new process for the given TDEApp.

        Args:
            TDE_App (type[TDEAppBase]): The app class to launch.
        """
        self.log(f"Requesting process launch for app: {TDE_App.APP_NAME}")

        # Launch the process asynchronously
        # TODO: this should be sync function + worker call
        await self._launch_process(TDE_App)

    def get_process_by_id(self, process_id: str) -> TDEAppBase:
        """
        Get a process by its ID.

        Args:
            process_id (str): The ID of the process to retrieve.
        Returns:
            TDEAppBase: The app instance associated with the given process ID.
        Raises:
            KeyError: If the process with the given ID does not exist.
        """
        if process_id not in self._processes:
            raise KeyError(f"Process with ID {process_id} does not exist.")
        return self._processes[process_id]

    ################
    # ~ Internal ~ #
    ################
    # This section is for methods that are only used internally
    # These should be marked with a leading underscore.

    def _add_process_to_dict(self, tde_app_instance: TDEAppBase, process_id: str) -> None:
        """
        Add a process to the app service's process dictionary.

        Args:
            tde_app_instance (TDEAppBase): The app instance to add.
            process_id (str): The ID of the app process.
        Raises:
            RuntimeError: If a process with the given ID already exists.
        """

        if process_id in self._processes:
            raise RuntimeError(f"Process with ID {process_id} already exists.")

        self._processes[process_id] = tde_app_instance
        self.log(f"Process {tde_app_instance.APP_NAME} with ID {process_id} added.")

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

    async def _launch_process(self, TDE_App: type[TDEAppBase]) -> None:
        """
        Args:
            TDE_App (TDEAppBase): The app to launch.
            Note that this is a class definition, not an instance.
        Raises:
            TypeError: If TDE_App is not a subclass of TDEAppBase.
            AssertionError: If the TDE_App is not valid (should never happen)
        Raises:
            RuntimeError: If a process with the given ID already exists.
        """
        self.log(f"Launching process for app: {TDE_App.APP_NAME}")

        assert issubclass(TDE_App, TDEAppBase)
        assert TDE_App.APP_NAME is not None
        assert TDE_App.APP_ID is not None

        # Get the app process ID with a number if needed.
        # This is to handle multiple instances of the same app.
        # Note that this is a simple identifier just for the App Process Service.
        # There is also a UID that is set on all types of processes in TDE.
        process_id = self._set_available_process_id(TDE_App.APP_ID)

        # * Create the app process instance
        # This is the instance of the base app inherited from the TDEAppBase class. Right now
        # it just holds all the app metadata. Store this in the process manager.
        app_process = TDE_App(process_id=process_id)
        try:
            self._add_process_to_dict(app_process, process_id)
        except RuntimeError as e:
            self.log.error(f"Failed to add process {process_id}: {e}")
            raise RuntimeError(
                f"Failed to add process {process_id} for app {TDE_App.APP_NAME}. "
                "This might be due to a duplicate process ID."
            ) from e

        app_context: ProcessContext = {
            "process_type": ProcessType.APP,
            "process_id": process_id,
            "process_uid": app_process.uid,
            "services": self.services_manager,
        }

        launch_mode = app_process.launch_mode()
        if launch_mode == LaunchMode.WINDOW:

            main_content = app_process.get_main_content()
            if main_content is None:
                self.log.error("The main_content property must return a Widget if your app is not a Daemon")
                #! Create error popup for user here
                return
            try:
                content_instance = main_content(app_context)
            except Exception as e:
                self.log.error(f"Failed to create main content instance for {app_process.APP_NAME}: {e}")
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
            self.log.error(f"Unknown launch mode {launch_mode} for app {app_process.APP_NAME}")
            #! Create error popup for user here
            return
