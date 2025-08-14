"""shells.py - The shell service for handling shells in TDE.

Note that this file is very similar to the `services/apps.py` file, as they both
use the same dynamic loading mechanism to scan for either shells or apps."""

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING, Awaitable, Callable  # , Any
import os
import importlib.util
from pathlib import Path
import asyncio

if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager

# Textual imports
from textual.worker import WorkerError

# Local imports
from term_desktop.services.servicebase import TDEServiceBase
from term_desktop.aceofbase import ProcessContext, ProcessType
from term_desktop.shell.shellbase import (
    TDEShellBase,
    TDEShellSession,
)


class ShellService(TDEServiceBase[TDEShellBase]):

    ################
    # ~ Messages ~ #
    ################
    # None yet

    #####################
    # ~ Initialzation ~ #
    #####################

    SERVICE_ID = "shell_service"

    def __init__(
        self,
        services_manager: ServicesManager,
    ) -> None:
        """
        Initialize the shell service.

        Args:
            services_manager (ServicesManager): The services manager instance.
        """
        super().__init__(services_manager)
        self.validate()
        self._registered_shells: dict[str, type[TDEShellBase]] = {}
        self._shell_session_dict: dict[str, TDEShellSession] = {}
        self._failed_shells: dict[str, Exception] = {}

        spec = importlib.util.find_spec("term_desktop.shells")
        if spec is not None and spec.submodule_search_locations:
            self._directories = [Path(next(iter(spec.submodule_search_locations)))]

    ################
    # ~ Contract ~ #
    ################

    async def start(self) -> bool:
        """Start the Shell service.
        If it returns True, the self.registered_shells dictionary will be available.

        Raises:
            RuntimeError: If the shell discovery fails or no shells are found.

        - Function is pure: [no]"""

        self.log("Starting ShellLoader service")
        self._failed_shells.clear()

        assert self.SERVICE_ID is not None
        worker_meta: ServicesManager.WorkerMeta = {
            "work": self._discover_shells,
            "name": "DiscoverShellsWorker",
            "service_id": self.SERVICE_ID,
            "group": self.SERVICE_ID,
            "description": "Discover shells in directories",
            "exit_on_error": False,
            "start": True,
            "exclusive": True,  # only 1 shell scan allowed at a time
            "thread": False,
        }
        worker = self.run_worker(self.directories, worker_meta=worker_meta)

        try:
            self._registered_shells = await worker.wait()
        except WorkerError as e:
            self.log.error(f"Failed to discover shells: {str(e)}")
            raise e
        else:
            if len(self.registered_shells) == 0:
                self.log.error("Loader 'worked', but no shells were discovered. Must have malfunctioned.")
                return True
            else:
                self.log.info(
                    f"Discovered {len(self.registered_shells)} shells: \n"
                    f"{', '.join(self.registered_shells.keys())}"
                )
            return True

    async def stop(self) -> bool:
        self.log("Stopping Shell Service")
        self._processes.clear()
        self._instance_counter.clear()
        self._registered_shells.clear()
        return True

    ####################
    # ~ External API ~ #
    ####################
    # Methods that might need to be accessed by
    # anything else in TDE, including other services.

    @property
    def registered_shells(self) -> dict[str, type[TDEShellBase]]:
        """
        Get the currently registered shells.

        Returns:
            Dictionary mshelling shell IDs to their shell classes.
        """
        return self._registered_shells

    @property
    def failed_shells(self) -> dict[str, Exception]:
        """
        Get the shells that failed to load.

        Returns:
            dict[str, Exception]: Dictionary mshelling shell IDs to the exceptions raised during loading.
        """
        return self._failed_shells

    @property
    def directories(self) -> list[Path]:
        """
        Get the list of directories where shells are searched for.

        Returns:
            list[Path]: List of directories to search for shell files.
        """
        return self._directories

    def add_directory(self, directory: Path) -> None:
        """
        Add a directory to the list of directories to search for shell files.

        Args:
            directory (Path): The directory to add.

        - Function is pure: [no]
        """
        assert isinstance(directory, Path), "directory must be a Path object"
        if not directory.exists():
            raise FileNotFoundError(f"Directory does not exist: {directory}")
        self._directories.append(directory)
        self.log.debug(f"Added shells directory: {directory}")

    def request_shell_launch(
        self,
        TDE_Shell: type[TDEShellBase],
    ) -> None:
        """
        Request the shell service to launch a new process for the given TDEShell.

        Args:
            TDE_Shell (type[TDEShellBase]): The shell class to launch.
        Raises:
            TypeError: If TDE_Shell is not a subclass of TDEShellBase.
            RuntimeError: If a process with the given ID already exists.
        """
        self.log(f"Requesting process launch for shell: {TDE_Shell.SHELL_NAME}")

        # More validation should go here in the future
        if not issubclass(TDE_Shell, TDEShellBase):  # type: ignore[unused-ignore]
            self.log.error(f"Invalid shell class: {TDE_Shell.__name__} is not a subclass of TDEShellBase")
            raise TypeError(f"{TDE_Shell.__name__} is not a valid TDEShellBase subclass")

        asyncio.create_task(self._launch_shell_runner(TDE_Shell))

    def register_mounting_callback(self, callback: Callable[[TDEShellSession], Awaitable[None]]) -> None:
        """This is used by the MainScreen class to register a
        callback that will be called when a new shell is mounted.

        Args:
            callback (Callable[[TDEShell], Awaitable[None]]): The callback function to
                be called when a new shell is mounted. The callback should accept a
                single argument, which is the shell being mounted.
        Raises:
            ValueError: If a callback with the same ID is already registered.
            ValueError: If the callback is not callable.
        """
        if not callable(callback):
            raise ValueError(f"Callback {callback} is not callable.")
        self._mounting_callback = callback

    def register_unmounting_callback(self, callback: Callable[[TDEShellSession], Awaitable[None]]) -> None:
        """This is used by the MainScreen Class to register a
        callback that will be called when a shell is unmounted.

        Args:
            callback (Callable[[TDEShell], Awaitable[None]]): The callback function to
                be called when a shell is unmounted. The callback should accept a
                single argument, which is the shell being unmounted.
        Raises:
            ValueError: If the callback is not callable.
        """
        if not callable(callback):
            raise ValueError(f"Callback {callback} is not callable.")
        self.unmounting_callback = callback

    def mount_default_shell(self) -> None:
        """
        Mount the default shell. This is used when no shell is specified or available.
        Raises:
            RuntimeError: If no shells are registered or if the default shell cannot be launched.
        """
        if not self.registered_shells:
            raise RuntimeError("No shells are registered. Cannot mount default shell.")

        # try to get the default shell class directly:
        try:
            default_shell_class = self.registered_shells["default_shell"]
        except KeyError:
            # if that fails, look for the first shell in the registered shells
            self.log.warning("No default shell found. Using the first registered shell instead.")
            self.log.debug("Registered shells: " + ", ".join(self.registered_shells.keys()))
            if not self.registered_shells:
                raise RuntimeError("No shells are registered. Cannot mount default shell.")
            default_shell_class = next(iter(self.registered_shells.values()))

        self.request_shell_launch(default_shell_class)

    ################
    # ~ Internal ~ #
    ################
    # These should be marked with a leading underscore.

    async def _launch_shell_runner(self, TDE_Shell: type[TDEShellBase]) -> None:

        assert TDE_Shell.SHELL_NAME is not None
        assert self.SERVICE_ID is not None
        worker_meta: ServicesManager.WorkerMeta = {
            "work": self._launch_shell,
            "name": "LaunchShellWorker-" + TDE_Shell.SHELL_NAME,
            "service_id": self.SERVICE_ID,
            "group": self.SERVICE_ID,
            "description": "Launch shell " + TDE_Shell.SHELL_NAME,
            "exit_on_error": False,
            "start": True,
            "exclusive": False,  # This is not an exclusive worker, multiple shells can be launched at once
            "thread": False,
        }
        worker = self.run_worker(TDE_Shell, worker_meta=worker_meta)
        try:
            await worker.wait()
        except WorkerError:
            self.log.error(f"Failed to launch shell {TDE_Shell.SHELL_NAME}")

    async def _launch_shell(self, TDE_Shell: type[TDEShellBase]) -> None:
        """
        Args:
            TDE_Shell (TDEShellBase): The shell to launch.
            Note that this is a class definition, not an instance.
        Raises:
            TypeError: If TDE_Shell is not a subclass of TDEShellBase.
            AssertionError: If the TDE_Shell is not valid (should never happen)
        Raises:
            RuntimeError: If a process with the given ID already exists.
        """
        self.log(f"Launching process for shell: {TDE_Shell.SHELL_NAME}")

        assert TDE_Shell.SHELL_NAME is not None
        assert TDE_Shell.SHELL_ID is not None

        # NOTE: Shells do not need to set an available process ID,
        # because only 1 shell is ever allowed to run at a time.
        process_id = TDE_Shell.SHELL_ID

        # Stage 1: Create the shell process instance
        try:
            shell_process = TDE_Shell()
        except Exception as e:
            raise RuntimeError(
                f"Error while creating shell process '{TDE_Shell.__class__.__name__}': {e}"
            ) from e

        # NOTE: Even though there can only ever be one shell process running at a time,
        # we will still add it to the process dictionary just to be consistent with
        # the way the other services work.

        # Stage 2: Add the shell process to the process dictionary
        try:
            self._add_process_to_dict(shell_process, process_id)
        except RuntimeError as e:
            raise RuntimeError(
                f"Failed to add process {process_id} for shell {TDE_Shell.SHELL_NAME}. "
                "This might be due to a duplicate process ID."
            ) from e

        # Stage 3: Create the shell context dictionary
        shell_context: ProcessContext = {
            "process_type": ProcessType.SHELL,
            "process_id": process_id,
            "process_uid": shell_process.uid,
            "services": self.services_manager,
        }

        # Stage 4: Get shell class definition from process instance
        try:
            tde_shell_session = shell_process.get_shell_session()
        except Exception as e:
            raise RuntimeError(
                f"Failed to get shell class from process {process_id} for shell {process_id}."
            ) from e

        # Stage 5: Create the shell instance
        try:
            shell_session_instance = tde_shell_session(shell_context)
        except Exception as e:
            raise RuntimeError(f"Failed to create shell instance for {process_id}: {e}") from e

        # Stage 7: Store the shell instance in the dictionary
        self._shell_session_dict[process_id] = shell_session_instance

        # Stage 8: Call the mounting callback with the new shell instance
        try:
            await self._mounting_callback(shell_session_instance)
        except Exception as e:
            raise RuntimeError(
                f"Error while executing callback '{self._mounting_callback}' "
                f"for shell '{TDE_Shell.__class__.__name__}': {e}"
            ) from e

        shell_session_instance.post_initialized()

    async def _discover_shells(self, directories: list[Path]) -> dict[str, type[TDEShellBase]]:
        """
        Scan the provided shell directories for shells and attempt to load them.

        Args:
            directories (list[Path]): List of directories to search for shell files.
        Returns:
            Dictionary mshelling shell names to their shell classes
        Raises:
            FileNotFoundError: If any of the directories do not exist.

        - Function is pure: [✓]
        """

        self.log.debug("Discovering shells")
        loaded_shells: dict[str, type[TDEShellBase]] = {}

        # These allowed names could be extended in the future. I thought it would be
        # good to code it in a way that allows for easy extension.
        allowed_main_names = {"shell.py"}

        # This is a dictionary where the key is the shell name, and the value is the path.
        shells_to_load: dict[str, Path] = {}

        for directory in directories:
            if not os.path.exists(directory):
                raise FileNotFoundError(f"Shells directory not found: {directory}")

            for path in Path(directory).iterdir():
                shell_path: Path | None = None
                if not path.name.startswith("__"):  # excludes __init__ and __pycache__

                    if path.is_dir():
                        for candidate in allowed_main_names:
                            if (path / candidate).exists():
                                shell_path = path
                                break
                        if shell_path is None:
                            self.log.warning(
                                f"Directory {path} does not contain a valid shell file. Skipping."
                            )
                            continue
                    else:
                        continue

                    if path.stem in shells_to_load:
                        self.log.error(f"Shell with name '{path.stem}' already exists. Skipping: {path}")
                        self._failed_shells[path.name] = ValueError("Duplicate shell name")
                        continue
                    shells_to_load[path.stem] = shell_path

        # Code reaching this point will have completed the discovery of shells.
        # If there were any shells with the same name, the conflicting shell was
        # blocked from being added to the shells_to_load dict.
        for _shell_name_, path in shells_to_load.items():

            try:
                ShellClass = self._load_shell_class(path)
            except ImportError as e:
                self.log.error(f"Failed to load shell {path.name}: {str(e)}")
                self._failed_shells[path.name] = e
                continue
            except Exception as e:
                self.log.error(f"Unexpected error loading shell {path.name}: {str(e)}")
                self._failed_shells[path.name] = e
                continue

            # ~ Validate the shell class ~ #
            try:
                ShellClass.validate()
            except NotImplementedError as e:
                self.log.error(f"Shell {ShellClass.__name__} failed validation: {str(e)}")
                self._failed_shells[path.name] = e
                continue

            assert ShellClass.SHELL_ID is not None  # validated above
            try:
                loaded_shells[ShellClass.SHELL_ID] = ShellClass
            except KeyError as e:
                #! NOTE: This should not be possible, as we check for duplicates above.
                self.log.error(
                    f"Shell was loaded successfully, but shell with ID "
                    f"{ShellClass.SHELL_ID} is already registered!"
                )
                self._failed_shells[path.name] = e

        return loaded_shells

    def _load_shell_class(self, path: Path) -> type[TDEShellBase]:
        """
        Load an shell class from a given path.
        Called by ShellLoader._discover_shells (above)

        Args:
            path (Path): Path to the shell file.
            file_or_dir (str): Type of the path, either 'file' or 'dir'.
        Returns:
            type[TDEShellBase]: The loaded shell class.
        Raises:
            ImportError: If the shell class cannot be loaded or does not implement the required interface.

        - Function is pure: [✓]
        """
        location = path / "shell.py"
        module_name = f"dynamic_pkg_{path.name}"

        ### ~ Stage 1: Load the module spec ~ ###
        try:
            spec = importlib.util.spec_from_file_location(module_name, location)
        except Exception as e:
            raise ImportError(f"Failed to load spec for shell {module_name}: {str(e)}") from e
        else:
            if spec is None or spec.loader is None:
                raise ImportError(f"Failed to load spec for shell {module_name}")

        ### ~ Stage 2: Load module using the spec ~ ###
        try:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            raise ImportError(f"Failed to load module for shell {module_name}: {str(e)}") from e

        ### ~ Stage 3: Retrieve the shell class from module ~ ###
        try:
            ShellClass = next(
                cls
                for _name_, cls in module.__dict__.items()
                if isinstance(cls, type) and issubclass(cls, TDEShellBase) and cls is not TDEShellBase
            )
        except StopIteration:
            raise ImportError(
                f"{module_name} did not return a valid TDEShellBase class."
                "Ensure that your main shell class inherits from TDEShellBase."
            )
        except Exception as e:
            raise ImportError(f"Failed to retrieve shell class from module {module_name}: {str(e)}") from e

        return ShellClass
