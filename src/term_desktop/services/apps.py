"""apps.py - The app service for handling apps in TDE.

Note that this file is very similar to the `services/shells.py` file, as they both
use the same dynamic loading mechanism to scan for either apps or shells."""

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING  # , Any
import os
import importlib.util
from pathlib import Path
import asyncio

if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager
    from term_desktop.services.windows import WindowService
    from term_desktop.app_sdk import TDEAppBase

# Textual imports
from textual.worker import WorkerError

# Local imports
from term_desktop.services.servicebase import TDEServiceBase
from term_desktop.aceofbase import ProcessContext, ProcessType
from term_desktop.app_sdk import LaunchMode
from term_desktop.app_sdk.appbase import (
    TDEAppBase,
    TDEMainWidget,
    DefaultWindowSettings,
)


class AppService(TDEServiceBase[TDEAppBase]):

    ################
    # ~ Messages ~ #
    ################
    # None yet

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
        self._registered_apps: dict[str, type[TDEAppBase]] = {}
        self._failed_apps: dict[str, Exception] = {}

        spec = importlib.util.find_spec("term_desktop.apps")
        if spec is not None and spec.submodule_search_locations:
            self._directories = [Path(next(iter(spec.submodule_search_locations)))]

    ################
    # ~ Contract ~ #
    ################

    async def start(self) -> bool:
        """Start the App service.
        If it returns True, the self.registered_apps dictionary will be available.

        Raises:
            RuntimeError: If the app discovery fails or no apps are found.

        - Function is pure: [no]"""

        self.log("Starting App service")
        self._failed_apps.clear()

        assert self.SERVICE_ID is not None
        worker_meta: ServicesManager.WorkerMeta = {
            "work": self._discover_apps,
            "name": "DiscoverAppsWorker",
            "service_id": self.SERVICE_ID,
            "group": self.SERVICE_ID,
            "description": "Discover apps in directories",
            "exit_on_error": False,
            "start": True,
            "exclusive": True,  # only 1 app scan allowed at a time
            "thread": False,
        }
        worker = self.run_worker(self.directories, worker_meta=worker_meta)

        try:
            self._registered_apps = await worker.wait()
        except WorkerError as e:
            self.log.error(f"Failed to discover apps: {str(e)}")
            raise e
        else:
            if len(self.registered_apps) == 0:
                self.log.error("Loader 'worked', but no apps were discovered. Must have malfunctioned.")
                return True
            else:
                self.log.info(
                    f"Discovered {len(self.registered_apps)} apps: \n"
                    f"{', '.join(self.registered_apps.keys())}"
                )
            return True

    async def stop(self) -> bool:
        self.log("Stopping App Service")
        self._processes.clear()
        self._instance_counter.clear()
        self._registered_apps.clear()
        return True

    ####################
    # ~ External API ~ #
    ####################
    # Methods that might need to be accessed by
    # anything else in TDE, including other services.

    @property
    def registered_apps(self) -> dict[str, type[TDEAppBase]]:
        """
        Get the currently registered apps.

        Returns:
            Dictionary mapping app IDs to their app classes.
        """
        return self._registered_apps

    @property
    def failed_apps(self) -> dict[str, Exception]:
        """
        Get the apps that failed to load.

        Returns:
            dict[str, Exception]: Dictionary mapping app IDs to the exceptions raised during loading.
        """
        return self._failed_apps

    @property
    def directories(self) -> list[Path]:
        """
        Get the list of directories where apps are searched for.

        Returns:
            list[Path]: List of directories to search for app files.
        """
        return self._directories

    @property
    def content_instance_dict(self) -> dict[str, TDEMainWidget]:
        """Get the dictionary of main content widgets for each app ID"""
        return self._content_instance_dict

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

        asyncio.create_task(self._launch_app_runner(TDE_App))

    def shutdown_app(self, app_id: str) -> None:
        """
        Shutdown an app by its ID.

        Args:
            app_id (str): The ID of the app to shutdown.
        Raises:
            KeyError: If the app with the given ID does not exist.
        """
        self.log(f"Shutting down app with ID: {app_id}")

        if app_id not in self._processes:
            raise KeyError(f"App with ID {app_id} does not exist.")

        app_process = self._processes[app_id]
        app_process.shutdown()
        self._remove_process(app_id)
        del self._content_instance_dict[app_id]
        self.log(f"App with ID {app_id} has been shut down and removed from the AppService.")

    def add_directory(self, directory: Path) -> None:
        """
        Add a directory to the list of directories to search for app files.

        Args:
            directory (Path): The directory to add.

        - Function is pure: [no]
        """
        assert isinstance(directory, Path), "directory must be a Path object"
        if not directory.exists():
            raise FileNotFoundError(f"Directory does not exist: {directory}")
        self._directories.append(directory)
        self.log.debug(f"Added apps directory: {directory}")

    ################
    # ~ Internal ~ #
    ################
    # These should be marked with a leading underscore.

    async def _launch_app_runner(self, TDE_App: type[TDEAppBase]) -> None:

        assert TDE_App.APP_NAME is not None
        assert self.SERVICE_ID is not None
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
        worker = self.run_worker(TDE_App, worker_meta=worker_meta)
        try:
            await worker.wait()
        except WorkerError:
            self.log.error(f"Failed to launch app {TDE_App.APP_NAME}")

    async def _launch_app(self, TDE_App: type[TDEAppBase]) -> None:
        """
        Args:
            TDE_App (TDEAppBase): The app to launch.
            Note that this is a class definition, not an instance.
        Raises:
            TypeError: If TDE_App is not a subclass of TDEAppBase.
            AssertionError: If the TDE_App is not valid (should never happen)
            RuntimeError: If anything goes wrong during the app launch process.
            (examine the exception message for details)
        """
        self.log(f"Launching process for app: {TDE_App.APP_NAME}")

        assert TDE_App.APP_NAME is not None
        assert TDE_App.APP_ID is not None

        # Stage 1: Set available process ID
        instance_num = self._get_available_instance_num(TDE_App.APP_ID)
        if instance_num == 1:
            process_id = TDE_App.APP_ID
        else:
            process_id = f"{TDE_App.APP_ID}_{instance_num}"

        # Stage 2: Create the app process instance
        try:
            app_process = TDE_App(process_id=process_id, instance_num=instance_num)
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
                    f"The main_content property of {app_process.APP_NAME} "
                    "must return a Widget if your app is not a Daemon"
                )

            # Stage 6: Create the main content instance
            try:
                content_instance = main_content(process_context=app_context)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to create main content instance for {app_process.APP_NAME}: {e}"
                ) from e
            if not isinstance(content_instance, TDEMainWidget):  # type: ignore[unused-ignore]
                raise RuntimeError(
                    f"The main content instance for {app_process.APP_NAME} "
                    "must be a subclass of TDEMainWidget"
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

            window_meta: WindowService.WindowMeta = {
                "content_instance": content_instance,
                "app_process_id": process_id,
                "window_dict": window_settings,
                "styles_dict": window_styles,
                "custom_mounts": custom_window_mounts,
                "callback_id": "main_desktop",  # This is the main desktop callback ID
            }

            await self.services_manager.window_service.request_new_window(window_meta=window_meta)

        elif launch_mode == LaunchMode.FULLSCREEN:
            pass  # coming soon

        elif launch_mode == LaunchMode.DAEMON:
            pass

        else:
            raise RuntimeError(
                f"Invalid launch mode for {TDE_App.APP_NAME}: {launch_mode}. "
                "Valid modes are: WINDOW, FULLSCREEN, DAEMON."
            )

    async def _discover_apps(self, directories: list[Path]) -> dict[str, type[TDEAppBase]]:
        """
        Scan the provided app directories for apps and attempt to load them.

        Args:
            directories (list[Path]): List of directories to search for app files.
        Returns:
            Dictionary mapping app names to their app classes
        Raises:
            FileNotFoundError: If any of the directories do not exist.

        - Function is pure: [✓]
        """

        self.log.debug("Discovering apps")
        loaded_apps: dict[str, type[TDEAppBase]] = {}

        # These allowed names could be extended in the future. I thought it would be
        # good to code it in a way that allows for easy extension.
        allowed_main_names = {"app.py", "main.py"}

        # This is a dictionary where the key is the app name, and the value is a tuple
        # containing the type of the path ('file' or 'dir') and the path itself.
        apps_to_load: dict[str, tuple[str, Path]] = {}

        for directory in directories:
            if not os.path.exists(directory):
                raise FileNotFoundError(f"Apps directory not found: {directory}")

            for path in Path(directory).iterdir():
                app_tuple: tuple[str, Path] | None = None
                if not path.name.startswith("__"):  # excludes __init__ and __pycache__

                    if path.is_file() and path.suffix == ".py":
                        app_tuple = ("file", path)
                    elif path.is_dir():
                        for candidate in allowed_main_names:
                            if (path / candidate).exists():
                                app_tuple = ("dir", path)
                                break
                        if app_tuple is None:
                            self.log.warning(f"Directory {path} does not contain a valid app file. Skipping.")
                            continue
                    else:
                        continue

                    if path.stem in apps_to_load:
                        self.log.error(f"App with name '{path.stem}' already exists. Skipping: {path}")
                        self._failed_apps[path.name] = ValueError("Duplicate app name")
                        continue
                    apps_to_load[path.stem] = app_tuple

        # Code at this point will be finished scanning *all* directories.
        # If there were any apps with the same name, the conflicting app was
        # blocked from being added to the apps_to_load dict.
        for _unique_key_, (file_or_dir, path) in apps_to_load.items():

            try:
                AppClass = self._load_app_class(path, file_or_dir)
            except ImportError as e:
                self.log.error(f"Failed to load app {path.name}: {str(e)}")
                self._failed_apps[path.name] = e
                continue
            except Exception as e:
                self.log.error(f"Unexpected error loading app {path.name}: {str(e)}")
                self._failed_apps[path.name] = e
                continue

            # ~ Validate the app class ~ #
            try:
                AppClass.validate()
            except NotImplementedError as e:
                self.log.error(f"App {AppClass.__name__} failed validation: {str(e)}")
                self._failed_apps[path.name] = e
                continue

            assert AppClass.APP_ID is not None  # validated above
            try:
                loaded_apps[AppClass.APP_ID] = AppClass
            except KeyError as e:
                #! NOTE: This should not be possible, as we check for duplicates above.
                self.log.error(
                    f"App was loaded successfully, but app with ID "
                    f"{AppClass.APP_ID} is already registered!"
                )
                self._failed_apps[path.name] = e

        return loaded_apps

    def _load_app_class(self, path: Path, file_or_dir: str) -> type[TDEAppBase]:
        """
        Load an app class from a given path.

        Args:
            path (Path): Path to the app file.
            file_or_dir (str): Type of the path, either 'file' or 'dir'.
        Returns:
            type[TDEAppBase]: The loaded app class.
        Raises:
            ImportError: If the app class cannot be loaded or does not implement the required interface.

        - Function is pure: [✓]
        """
        if file_or_dir == "file":
            location = path
            module_name = f"dynamic_mod_{path.stem}"
        else:
            assert file_or_dir == "dir"
            location = path / "app.py"
            module_name = f"dynamic_pkg_{path.name}"

        ### ~ Stage 1: Load the module spec ~ ###
        try:
            spec = importlib.util.spec_from_file_location(module_name, location)
        except Exception as e:
            raise ImportError(f"Failed to load spec for app {module_name}: {str(e)}") from e
        else:
            if spec is None or spec.loader is None:
                raise ImportError(f"Failed to load spec for app {module_name}")

        ### ~ Stage 2: Load module using the spec ~ ###
        try:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            raise ImportError(f"Failed to load module for app {module_name}: {str(e)}") from e

        ### ~ Stage 3: Retrieve the app class from module ~ ###
        try:
            AppClass = next(
                cls
                for _name_, cls in module.__dict__.items()
                if isinstance(cls, type) and issubclass(cls, TDEAppBase) and cls is not TDEAppBase
            )
        except StopIteration:
            raise ImportError(
                f"{module_name} did not return a valid TDEAppBase class."
                "Ensure that your main app class inherits from TDEAppBase."
            )
        except Exception as e:
            raise ImportError(f"Failed to retrieve app class from module {module_name}: {str(e)}") from e

        return AppClass
