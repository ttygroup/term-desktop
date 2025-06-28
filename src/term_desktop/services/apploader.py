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
        Initialize the app loader.
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

        #! MUST BE RE-WORKED TO ACCOMODATE PACKAGES INSTEAD OF ONLY .py FILES !!

        log.debug("Discovering apps")
        loaded_apps: dict[str, Type[TDEApp]] = {}

        for directory in directories:
            if not os.path.exists(directory):
                raise FileNotFoundError(f"Apps directory not found: {directory}")

            for path in Path(directory).iterdir():
                if path.suffix == ".py" and not path.name.startswith("__"):
                    log.debug(f"Found app file: {path.name}")

                    try:
                        AppClass = self.load_app_class(path)
                    except ImportError as e:
                        log.error(f"Failed to load app {path.name}: {str(e)}")
                        self._failed_apps[path.name] = e
                        continue
                    except Exception as e:
                        log.error(f"Unexpected error loading app {path.name}: {str(e)}")
                        self._failed_apps[path.name] = e
                        continue

                    log(f"Loaded app class: {AppClass.__name__} from {path.name}")

                    assert AppClass.APP_ID is not None  # validated by the TDEApp ABC
                    try:
                        loaded_apps[AppClass.APP_ID] = AppClass
                    except KeyError:
                        log.error(
                            f"App was loaded successfully, but app with ID "
                            f"{AppClass.APP_ID} is already registered!"
                        )
                        self._failed_apps[path.name] = KeyError(
                            f"App with ID {AppClass.APP_ID} already registered."
                        )
                    else:
                        log.debug(f"Loaded app: {AppClass.APP_NAME}")

        return loaded_apps

    def load_app_class(self, path: Path) -> Type[TDEApp]:
        """
        Load an app class from a given path.
        Called by AppLoader.discover_apps (above)

        Args:
            path (Path): Path to the app file.
        Returns:
            Type[TDEApp]: The loaded app class.
        Raises:
            ImportError: If the app class cannot be loaded or does not implement the required interface.

        - Function is pure: [✓]   
        """

        ### ~ Stage 1: Load the module spec ~ ###
        try:
            spec = importlib.util.spec_from_file_location(path.stem, path)
        except Exception as e:
            raise ImportError(f"Failed to load spec for app {path.stem}: {str(e)}") from e
        else:
            if spec is None or spec.loader is None:
                raise ImportError(f"Failed to load spec for app {path.stem}")

        ### ~ Stage 2: Load module using the spec ~ ###
        try:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            raise ImportError(f"Failed to load module for app {path.stem}: {str(e)}") from e

        ### ~ Stage 3: Retrieve the app class from module ~ ###
        # new plan: get dict of all classes in the module, then check for TDEApp subclass
        try:
            AppClass = next(
                cls for _name_, cls in module.__dict__.items()
                if isinstance(cls, type) and issubclass(cls, TDEApp) and cls is not TDEApp
            )
        except StopIteration:
            raise ImportError(
                f"{path.stem} did not return a valid TDEApp class."
                "Ensure that your main app class inherits from TDEApp."
            )
        return AppClass
