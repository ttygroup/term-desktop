"servicebase.py - base class for all services in TDE."

from __future__ import annotations
from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar, Generic, Any  # , Callable, TypedDict

if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager
    from textual.worker import Worker
    from textual.message import Message

# Textual imports
# from textual.worker import NoActiveWorker, WorkerError

# Local imports
from term_desktop.aceofbase import AceOfBase

# Having this be a top-level constant is maybe not the best
# way to handle this but it'll do for now.
VALID_PROCESS_ID_TYPES = ["APP_ID", "SCREEN_ID", "SHELL_ID", "WINDOW_ID"]


TDEProcess = TypeVar("TDEProcess", bound=AceOfBase)


class TDEServiceBase(AceOfBase, Generic[TDEProcess]):

    # NOTE: services don't require a context dictionary on the services manager.
    # The service manager is just attached directly. They can afford to be a bit
    # more tightly coupled compared to other components like apps, screens, or shells.

    SERVICE_ID: str | None = None

    def __init__(self, services_manager: ServicesManager) -> None:
        self.services_manager = services_manager
        self._processes: dict[str, TDEProcess] = {}
        self._instance_counter: dict[str, set[int]] = {}

    @classmethod
    def validate(cls) -> None:

        required_members = {
            "SERVICE_ID": "class attribute",
            # more will go here as needed
        }
        cls.validate_stage1()
        cls.validate_stage2(required_members)

    @property
    def processes(self) -> dict[str, TDEProcess]:
        """Get the currently running app processes."""
        return self._processes

    @property
    def instance_counter(self) -> dict[str, set[int]]:
        """Get the instance counter for each app ID."""
        return self._instance_counter

    ################
    # ~ Contract ~ #
    ################

    @abstractmethod
    async def start(self) -> bool: ...

    @abstractmethod
    async def stop(self) -> bool: ...

    #######################
    # ~ Process Methods ~ #
    #######################

    def _add_process_to_dict(self, tde_process_instance: TDEProcess, process_id: str) -> None:
        """
        Add a process instance to the service's process dictionary.

        Args:
            tde_process_instance (TDEProcess): The process instance to add.
            process_id (str): The ID of the process.
        Raises:
            RuntimeError: If a process with the given ID already exists.
        """

        if process_id in self._processes:
            raise RuntimeError(f"Process with ID {process_id} already exists.")

        self._processes[process_id] = tde_process_instance
        self.log(
            f"Process {process_id} with type {tde_process_instance.__class__.__name__} "
            f"added to {self.SERVICE_ID}."
        )

    def _remove_process(self, process_id: str) -> None:
        """
        Remove a process from the service's process dictionary.
        Args:
            process_id (str): The ID of the process to remove.
        Raises:
            KeyError: If the process with the given ID does not exist.
        """

        try:
            process = self._processes[process_id]
        except KeyError as e:
            self.log(f"Process with ID {process_id} does not exist in {self.SERVICE_ID}.")
            raise e
        else:
            for id_type in VALID_PROCESS_ID_TYPES:
                plain_id = getattr(process, id_type, None)

                # This is just to remove from the instance counter, if present
                if plain_id is not None and plain_id in self._instance_counter:
                    current_set = self._instance_counter[plain_id]
                    instance_num = getattr(process, "instance_num", None)
                    if instance_num is not None and instance_num in current_set:
                        current_set.remove(instance_num)
                        if not current_set:
                            del self._instance_counter[plain_id]  # remove empty set

            del self._processes[process_id]  # remove from dict
            self.log(f"Process {process_id} removed from {self.SERVICE_ID}.")

    def _get_available_instance_num(self, plain_id: str) -> int:

        current_set = self._instance_counter.get(plain_id, set())

        i = 1
        while i in current_set:
            i += 1
        current_set.add(i)
        return i

    #! Not used by anything yet
    def get_process_by_id(self, process_id: str) -> TDEProcess:
        """
        Get an app process by its ID.

        Args:
            process_id (str): The ID of the app process to retrieve.
        Returns:
            TDEAppBase: The app instance associated with the given process ID.
        Raises:
            KeyError: If the process with the given ID does not exist.
        """
        if process_id not in self._processes:
            raise KeyError(f"Process with ID {process_id} does not exist.")
        return self._processes[process_id]

    ######################
    # ~ Bridge Methods ~ #
    ######################
    # These are all methods that bridge to a corresponding method on the
    # services manager. Since base classes are not Textual objects, they do not have
    # access to textual abilities like run worker, post message, or log to console.
    # Also, since all service workers run on the service manager class, that
    # creates a central place to monitor and control them.

    def run_worker(
        self,
        *args: Any,
        worker_meta: ServicesManager.WorkerMeta,
        **kwargs: Any,
    ) -> Worker[Any]:
        """
        Run a worker function on the services manager.

        Positional and keyword arguments are passed to the work function, which
        is the "work" key in the worker_meta dictionary.

        So for example if you pass in something like:
        `worker = self.run_worker(window_meta, worker_meta=worker_meta)`

        ...then the `window_meta` dictionary will be passed to the work function
        as its first positional argument. This uses functools.partial under the hood:
        `partial(worker_meta["work"], *args, **kwargs)`

        Note that this is a bridge function to the actual `run_worker` method
        of the `ServicesManager`. Services are not Textual objects and are not
        able to run workers themselves.

        Returns:
            Worker[Any]: The worker instance that was started.
        """
        return self.services_manager.run_worker(*args, worker_meta=worker_meta, **kwargs)

    def post_message(self, message: Message) -> None:
        """
        Post a message to the services manager. This will bubble up to
        the main App class.
        """
        self.services_manager.post_message(message)
