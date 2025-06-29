# Python imports
from __future__ import annotations
from typing import TYPE_CHECKING, Type
import os
import importlib.util
from pathlib import Path

if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager

# Textual imports
from textual import log

# Local imports
import term_desktop.apps
from term_desktop.app_sdk.appbase import TDEApp
from term_desktop.services.servicebase import BaseService


class AppLoader(BaseService):

    def __init__(
        self,
        services_manager: ServicesManager,
    ) -> None:
        """
        Initialize the app loader. Adds the default built-in apps directory
        to the list of directories to search for app files.
        """
        super().__init__(services_manager)
        self.directories: list[Path] = []
        self._registered_apps: dict[str, Type[TDEApp]] = {}
        self._failed_apps: dict[str, Exception] = {}

        builtin_apps = next(iter(term_desktop.apps.__path__))
        self.directories.extend([Path(builtin_apps)])

    @property
    def registered_apps(self) -> dict[str, Type[TDEApp]]:
        """
        Get the currently registered apps.

        Returns:
            dict[str, Type[TDEApp]]: Dictionary mapping app IDs to their app classes.
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
        self.directories.append(directory)
        log.debug(f"Added apps directory: {directory}")

    async def start(self) -> bool:
        """Start the AppLoader service.
        If it returns True, the self.registered_apps dictionary will be available.

        Raises:
            RuntimeError: If the app discovery fails or no apps are found.

        - Function is pure: [no]"""
        log("Starting AppLoader service")

        try:
            self._failed_apps.clear()
            self._registered_apps = await self.discover_apps(self.directories)
        except Exception as e:
            log.error(f"Failed to discover apps: {str(e)}")
            raise RuntimeError("AppLoader failed to start due to an error.") from e
        else:
            if len(self.registered_apps) == 0:
                log.error("Loader 'worked', but no apps were discovered. Must have malfunctioned.")
                return True
            else:
                log.info(f"Discovered {len(self.registered_apps)} apps")
                for app_id, app_class in self.registered_apps.items():
                    log.debug(f"ID: {app_id} - Display Name: {app_class.APP_NAME}")
            return True

    async def stop(self) -> bool:
        log("Stopping AppLoader service")
        self.registered_apps.clear()
        return True

    async def discover_apps(self, directories: list[Path]) -> dict[str, Type[TDEApp]]:
        """
        Scan the provided app directories for apps and attempt to load them.
        Called by AppLoader.start() (above)

        Args:
            directories (list[Path]): List of directories to search for app files.
        Returns:
            Dictionary mapping app names to their app classes
        Raises:
            FileNotFoundError: If any of the directories do not exist.

        - Function is pure: [✓]
        """

        log.debug("Discovering apps")
        loaded_apps: dict[str, Type[TDEApp]] = {}

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
                            log.warning(f"Directory {path} does not contain a valid app file. Skipping.")
                            continue
                    else:
                        continue

                    if path.stem in apps_to_load:
                        log.error(f"App with name '{path.stem}' already exists. Skipping: {path}")
                        self._failed_apps[path.name] = ValueError("Duplicate app name")
                        continue
                    apps_to_load[path.stem] = app_tuple

        # Code at this point will be finished scanning *all* directories.
        # If there were any apps with the same name, the conflicting app was
        # blocked from being added to the apps_to_load dict.
        for _unique_key_, (file_or_dir, path) in apps_to_load.items():

            try:
                AppClass = self.load_app_class(path, file_or_dir)
            except ImportError as e:
                log.error(f"Failed to load app {path.name}: {str(e)}")
                self._failed_apps[path.name] = e
                continue
            except Exception as e:
                log.error(f"Unexpected error loading app {path.name}: {str(e)}")
                self._failed_apps[path.name] = e
                continue

            assert AppClass.APP_ID is not None  # validated by the TDEApp ABC
            try:
                loaded_apps[AppClass.APP_ID] = AppClass
            except KeyError as e:
                log.error(
                    f"App was loaded successfully, but app with ID "
                    f"{AppClass.APP_ID} is already registered!"
                )
                self._failed_apps[path.name] = e

        return loaded_apps

    def load_app_class(self, path: Path, file_or_dir: str) -> Type[TDEApp]:
        """
        Load an app class from a given path.
        Called by AppLoader.discover_apps (above)

        Args:
            path (Path): Path to the app file.
            file_or_dir (str): Type of the path, either 'file' or 'dir'.
        Returns:
            Type[TDEApp]: The loaded app class.
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
        # new plan: get dict of all classes in the module, then check for TDEApp subclass
        try:
            AppClass = next(
                cls
                for _name_, cls in module.__dict__.items()
                if isinstance(cls, type) and issubclass(cls, TDEApp) and cls is not TDEApp
            )
        except StopIteration:
            raise ImportError(
                f"{module_name} did not return a valid TDEApp class."
                "Ensure that your main app class inherits from TDEApp."
            )
        return AppClass
