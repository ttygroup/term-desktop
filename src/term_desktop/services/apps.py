"processes.py - The app service for handling processes in TDE."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING  # , Any

if TYPE_CHECKING:
    # from textual.worker import Worker
    from term_desktop.services.manager import ServicesManager

# Textual imports
# from textual.worker import WorkerError

# Local imports
from term_desktop.services.servicebase import TDEServiceBase
from term_desktop.app_sdk import LaunchMode
from term_desktop.aceofbase import ProcessContext, ProcessType
from term_desktop.app_sdk.appbase import (
    TDEAppBase,
    DefaultWindowSettings,
    TDEMainWidget,
)

class AppService(TDEServiceBase):

    #####################
    # ~ Initialzation ~ #
    #####################

    SERVICE_ID = "app_service"

    def __init__(
        self,
        services_manager: ServicesManager,
    ) -> None:
        """
        Initialize the app service.

        Args:
            services_manager (ServicesManager): The services manager instance.
        """
        super().__init__(services_manager)
        self.validate()
        self._content_instance_dict: dict[str, TDEMainWidget] = {}

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
    def content_instance_dict(self) -> dict[str, TDEMainWidget]:
        """Get the dictionary of main content widgets for each app ID"""
        return self._content_instance_dict

    async def start(self) -> bool:
        self.log("Starting App Service")
        # Nothing to do here yet.
        return True

    async def stop(self) -> bool:
        self.log("Stopping App Service")
        self._processes.clear()
        self._instance_counter.clear()
        return True

    def request_app_launch(
        self,
        TDE_App: type[TDEAppBase],
    ) -> None:
        """
        Request the app service to launch a new process for the given TDEApp.

        Args:
            TDE_App (type[TDEAppBase]): The app class to launch.
        Raises:
            TypeError: If TDE_App is not a subclass of TDEAppBase.
            RuntimeError: If a process with the given ID already exists.
        """
        self.log(f"Requesting process launch for app: {TDE_App.APP_NAME}")

        # More validation should go here in the future
        if not issubclass(TDE_App, TDEAppBase):  # type: ignore[unused-ignore]
            self.log.error(f"Invalid app class: {TDE_App.__name__} is not a subclass of TDEAppBase")
            raise TypeError(f"{TDE_App.__name__} is not a valid TDEAppBase subclass")

        assert TDE_App.APP_NAME is not None
        worker_meta: ServicesManager.WorkerMeta = {
            "work": self._launch_app,
            "name": "LaunchAppWorker-" + TDE_App.APP_NAME,
            "service_id": self.SERVICE_ID,
            "group": self.SERVICE_ID,
            "description": "Launch app " + TDE_App.APP_NAME,
            "exit_on_error": False,
            "start": True,
            "exclusive": False,  # This is not an exclusive worker, multiple apps can be launched at once
            "thread": False,
        }
        self.run_worker(TDE_App, worker_meta=worker_meta)

    ################
    # ~ Internal ~ #
    ################
    # This section is for methods that are only used internally
    # These should be marked with a leading underscore.

    async def _launch_app(self, TDE_App: type[TDEAppBase]) -> None:
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

        assert TDE_App.APP_NAME is not None
        assert TDE_App.APP_ID is not None

        # Stage 1: Set available process ID
        process_id = self._set_available_process_id(TDE_App.APP_ID)

        # Stage 2: Create the app process instance
        try:
            app_process = TDE_App(process_id=process_id)
        except Exception as e:
            raise RuntimeError(f"Error while creating app process '{TDE_App.__class__.__name__}': {e}") from e

        # Stage 3: Add the app process to the process dictionary
        try:
            self._add_process_to_dict(app_process, process_id)
        except RuntimeError as e:
            raise RuntimeError(
                f"Failed to add process {process_id} for app {TDE_App.APP_NAME}. "
                "This might be due to a duplicate process ID."
            ) from e

        # Stage 4: Create the app context dictionary
        app_context: ProcessContext = {
            "process_type": ProcessType.APP,
            "process_id": process_id,
            "process_uid": app_process.uid,
            "services": self.services_manager,
        }

        launch_mode = app_process.launch_mode()
        if launch_mode == LaunchMode.WINDOW:

            # Stage 5: Get content class definition from process instance
            main_content = app_process.get_main_content()
            if main_content is None:
                raise RuntimeError(
                    f"The main_content property of {app_process.APP_NAME} must return a Widget if your app is not a Daemon"
                )

            # Stage 6: Create the main content instance
            try:
                content_instance = main_content(app_context)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to create main content instance for {app_process.APP_NAME}: {e}"
                ) from e
            if not isinstance(content_instance, TDEMainWidget):  # type: ignore
                raise RuntimeError(
                    f"The main content instance for {app_process.APP_NAME} must be a subclass of TDEMainWidget"
                )

            # Stage 7: Store the main content instance in the dictionary
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

            #! NOTE: The Window Service has not been rebuilt yet to use
            #! the window base

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
            raise RuntimeError(
                f"Invalid launch mode for {TDE_App.APP_NAME}: {launch_mode}. "
                "Valid modes are: WINDOW, FULLSCREEN, DAEMON."
            )
