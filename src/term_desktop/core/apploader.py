# Python imports
from __future__ import annotations
from typing import TYPE_CHECKING, Type, Dict

if TYPE_CHECKING:
    from term_desktop.main import TermDesktop

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from term_desktop.main import TermDesktop

import os
import importlib.util
from pathlib import Path

# Textual imports
from textual import log

# Local imports
from term_desktop.appbase import TermDApp
import term_desktop.apps


class AppLoader:

    # * Called by: load_apps in TermDesktop class.
    def __init__(self, directories: list[Path] | None = None) -> None:
        """
        Initialize the app loader with one or more app directories.

        Args:
            directories: List of directories to search for app files.
        """
        super().__init__()
        self.loaded_apps: Dict[str, Type[TermDApp]] = {}
        self.directories: list[Path] = []

        try:
            pkg_path: list[str] = getattr(term_desktop.apps, "__path__")
        except AttributeError as e:
            raise AttributeError(
                "Could not find the package path for term_desktop.apps. "
                "Ensure that term_desktop.apps is a valid package."
            ) from e

        default_path = Path(pkg_path[0])
        if not default_path.exists():
            raise FileNotFoundError(f"Apps directory not found: {default_path}")

        self.directories.extend([default_path])
        if directories:
            self.directories.extend(directories)

    called_by: list[TermDesktop]  # load_apps method

    def discover_apps(self) -> Dict[str, Type[TermDApp]]:
        """
        Scan all app directories for .py files and attempt to load them.

        Returns:
            Dictionary mapping app names to their app classes
        """
        log.debug("Discovering apps")

        self.loaded_apps.clear()

        for directory in self.directories:
            if not os.path.exists(directory):
                raise FileNotFoundError(f"Apps directory not found: {directory}")

            for path in Path(directory).iterdir():
                if path.suffix == ".py" and not path.name.startswith("__"):
                    log.debug(f"Found app file: {path.name}")

                    try:
                        AppClass = self.load_app_class(path)
                    except ImportError as e:
                        log.error(f"Failed to load app {path.name}: {str(e)}")
                        continue
                    except Exception as e:
                        log.error(f"Unexpected error loading app {path.name}: {str(e)}")
                        continue

                    assert AppClass.APP_ID is not None  # validated in above method
                    try:
                        self.loaded_apps[AppClass.APP_ID] = AppClass
                    except KeyError:
                        log.error(
                            f"App was loaded successfully, but app with ID "
                            f"{AppClass.APP_ID} is already registered!"
                        )
                    else:
                        log.debug(f"Loaded app: {AppClass.APP_NAME}")

        return self.loaded_apps

    # * called_by: AppLoader.discover_apps, above
    def load_app_class(self, path: Path) -> Type[TermDApp]:
        """
        Load an app class from a given path.

        Args:
            path (Path): Path to the app file.
        Returns:
            Type[TermDApp]: The loaded app class.
        Raises:
            ImportError: If the app class cannot be loaded or does not implement the required interface.
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

        ### ~ Stage 3: Retrieve the app class from loader ~ ###
        if not hasattr(module, "loader"):
            raise ImportError(
                f"Module for app {path.stem} does not have a loader function."
                "You require a function named `loader` at the top level of your module."
                "Please see the documentation for more info: {INSERT LINK HERE}"
            )
        try:
            AppClass = module.loader()  # ? Returns Class Definition, NOT an instance.
        except Exception as e:
            raise ImportError(f"App {path.stem} loader function raised an error: {str(e)}") from e

        ### ~ Stage 4: Validate the app class interface and return ~ ###
        if not issubclass(AppClass, TermDApp):
            raise ImportError("Loader function worked, but the class returned is not a valid TermDApp class")
        if not isinstance(AppClass, type):  # type: ignore[unused-ignore] Pyright thinks this is unnecessary.
            raise ImportError(
                f"Loader function for app {path.stem} did not return a class definition."
                "Ensure that your loader function returns a class definition, not an instance."
            )
        try:
            AppClass.validate_interface()  # This is a class method
        except Exception as e:
            raise ImportError(f"App {path.stem} does not implement the required interface: {str(e)}") from e
        else:
            return AppClass
