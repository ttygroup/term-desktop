"manager.py - Uber manager of services."

# python standard library imports
from __future__ import annotations
from dataclasses import dataclass
from typing import TypedDict, Callable, Any, cast, TYPE_CHECKING
from functools import partial
from time import time
from pathlib import Path
import platformdirs
if TYPE_CHECKING:
    import rich.repr

# from logging import Logger
# from ezpubsub import Signal


# Textual imports
from textual import on
from textual.message import Message
from textual.worker import Worker, WorkerState
from textual.widget import Widget
from rich.text import Text

# Local imports
from term_desktop.services.servicebase import TDEServiceBase
from term_desktop.services.tde_logging import LoggingService
from term_desktop.services.apps import AppService
from term_desktop.services.windows import WindowService
from term_desktop.services.screens import ScreenService
from term_desktop.services.shells import ShellService
from term_desktop.services.databases import DatabaseService
from term_desktop.services.fileassociations import FileAssociationService


class ServicesManager(Widget):
    """The uber manager to manage other managers.

    This is a Textual Widget because it will allow it to do Textual things
    like run workers or send messages to the main app.
    """

    SERVICE_ID = "services_manager"

    class WorkerMeta(TypedDict):
        """WorkerMeta is required to run work on the ServicesManager.

        Required keys:
        - work: Callable[..., Any]
        - name: str
        - service_id: str
        - group: str
        - description: str
        - exit_on_error: bool
        - start: bool
        - exclusive: bool
        - thread: bool
        """

        work: Callable[..., Any]
        name: str
        service_id: str
        group: str
        description: str
        exit_on_error: bool
        start: bool
        exclusive: bool
        thread: bool

    class ActiveWorkerInfo(TypedDict):
        meta: ServicesManager.WorkerMeta
        service_id: str
        start_time: float
        status: WorkerState

    class ServicesStarted(Message):
        """Message to indicate that all services have been started."""

        def __init__(self) -> None:
            super().__init__()

    @dataclass(frozen=True)
    class Services:
        logging_service: LoggingService
        shell_service: ShellService
        screen_service: ScreenService
        window_service: WindowService
        app_service: AppService
        database_service: DatabaseService
        file_association_service: FileAssociationService
        
    initialized = False

    def __init__(self) -> None:
        super().__init__()

        # display = False to make this a non-visible background widget.
        self.display = False

        self.storage_dir = Path(
            platformdirs.user_data_dir(appname="term-desktop", ensure_exists=True)
        )
        """ServicesManager storage directory. Use this as the path for any services
        that need to store data on disk."""

        # _active_workers is a dict that maps
        # worker IDs to tuples of (worker name, service ID, start time)
        # self._active_workers: dict[str, tuple[str, str, float]] = {}
        self._active_workers: dict[str, ServicesManager.ActiveWorkerInfo] = {}

        # Note that Textual's built in Worker Manager also keeps an internal list of workers,
        # but this is needed to let us track workers by other metrics, such as start time
        # or the service it belongs to.

        # This is a debounce flag to prevent
        # _check_running_workers from being called too frequently:
        self._worker_check_pending = False
        
        try:
            logging_service = LoggingService(self)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize LoggingService: {str(e)}") from e
        
        try:
            shell_service = ShellService(self)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ShellService: {str(e)}") from e
        
        try:
            screen_service = ScreenService(self)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ScreenService: {str(e)}") from e
        
        try:
            window_service = WindowService(self)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize WindowService: {str(e)}") from e
        
        try:
            app_service = AppService(self)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AppService: {str(e)}") from e
        
        try:
            database_service = DatabaseService(self)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize DatabaseService: {str(e)}") from e
        
        try:
            file_association_service = FileAssociationService(self)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize FileAssociationService: {str(e)}") from e
        
        self._services = ServicesManager.Services(
            logging_service = logging_service,
            shell_service = shell_service,
            screen_service = screen_service,
            window_service = window_service,
            app_service = app_service,
            database_service = database_service,
            file_association_service = file_association_service,
        )  
        
        self.initialized = True

    def __rich_repr__(self) -> rich.repr.Result:
        if self.initialized:
            yield f"{self.logging_service.SERVICE_ID}: \n", self.logging_service.processes.keys()
            yield f"{self.shell_service.SERVICE_ID}: \n", self.shell_service.processes.keys()
            yield f"{self.screen_service.SERVICE_ID}: \n", self.screen_service.processes.keys()
            yield f"{self.window_service.SERVICE_ID}: \n", self.window_service.processes.keys()
            yield f"{self.app_service.SERVICE_ID}: \n", self.app_service.processes.keys()
            yield f"{self.database_service.SERVICE_ID}: \n", self.database_service.processes.keys()
        else:
            yield "ServicesManager not initialized"

    ##################
    # ~ Properties ~ #
    ##################
    
    @property
    def services(self) -> Services:
        """Access all services."""
        return self._services
    
    @property
    def logging_service(self) -> LoggingService:
        """Access the Logging Service."""
        return self._services.logging_service

    @property
    def shell_service(self) -> ShellService:
        """Access the Shell Service."""
        return self._services.shell_service

    @property
    def screen_service(self) -> ScreenService:
        """Access the Screen Service."""
        return self._services.screen_service

    @property
    def window_service(self) -> WindowService:
        """Access the Window Service."""
        return self._services.window_service

    @property
    def app_service(self) -> AppService:
        """Access the App Service."""
        return self._services.app_service

    @property
    def database_service(self) -> DatabaseService:
        """Access the Database Service."""
        return self._services.database_service

    @property
    def fileassociation_service(self) -> FileAssociationService:
        """Access the File Association Service."""
        return self._services.file_association_service

    @property
    def active_workers(self) -> dict[str, ServicesManager.ActiveWorkerInfo]:
        """A dictionary of active workers with their IDs, names, service IDs,
        and start times."""
        return self._active_workers

    ####################
    # ~ External API ~ #
    ####################

    async def start_all_services(self) -> None:
        """Start all services."""

        worker_meta: ServicesManager.WorkerMeta = {
            "work": self._start_all_services,
            "name": "StartAllServices",
            "service_id": self.SERVICE_ID,
            "group": self.SERVICE_ID,
            "description": "Start all services in the ServicesManager.",
            "exit_on_error": True,
            "start": True,
            "exclusive": True,
            "thread": False,
        }
        try:
            worker: Worker[bool] = self.run_worker(worker_meta=worker_meta)
            await worker.wait()
        except Exception as e:
            raise e

    #! Override
    def run_worker(  # type: ignore
        self,
        *args: Any,
        worker_meta: WorkerMeta,
        **kwargs: Any,
    ) -> Worker[Any]:
        """
        Run a worker function on the services manager.

        Positional and keyword arguments are passed to the work function
        (the "work" key in the worker_meta dictionary).

        Note that this is a bridge function to the actual `run_worker` method
        of the `ServicesManager`. Services are not Textual objects and are not
        able to run workers themselves.

        Returns:
            Worker[Any]: The worker instance that was started.
        """

        # Validate required keys are present in worker_meta
        required_keys = {
            "work",
            "name",
            "service_id",
            "group",
            "description",
            "exit_on_error",
            "start",
            "exclusive",
            "thread",
        }
        if not required_keys.issubset(worker_meta.keys()):
            missing_keys = required_keys - worker_meta.keys()
            raise TypeError(f"worker_meta is missing required keys: {missing_keys}")

        partial_func = partial(worker_meta["work"], *args, **kwargs)
        worker = super().run_worker(
            work=partial_func,
            name=worker_meta["name"],
            group=worker_meta["group"],
            description=worker_meta["description"],
            exit_on_error=worker_meta["exit_on_error"],
            start=worker_meta["start"],
            exclusive=worker_meta["exclusive"],
            thread=worker_meta["thread"],
        )

        service_id = worker_meta["service_id"]
        worker_id = f"{id(worker)}"
        start_time = time()
        active_worker_info: ServicesManager.ActiveWorkerInfo = {
            "meta": worker_meta,
            "service_id": worker_meta["service_id"],
            "start_time": start_time,
            "status": WorkerState.PENDING,
        }

        #! This dictionary is not actually used by anything right now. It just exists.
        self._active_workers[worker_id] = active_worker_info

        # These attributes are assigned directly onto the worker instance:
        setattr(worker, "service_id", service_id)
        setattr(worker, "worker_id", worker_id)
        setattr(worker, "start_time", start_time)
        return worker

    ################
    # ~ Internal ~ #
    ################

    async def _start_all_services(self) -> bool | None:
        """
        # ? This will eventually be built out to have some kind of monitoring
        # system to watch the state of active services, stop/restart them, etc.
        """

        # Using the services dataclass as the source of truth for what services exist.
        # Prevents code duplication in this method.
        for service_name, service in self._services.__dict__.items():
            try:
                assert isinstance(service, TDEServiceBase)
                service_success = await service.start()
            except RuntimeError:
                raise
            except Exception as e:
                raise RuntimeError(
                    f"{service_name} startup failed with an unexpected error: {str(e)}"
                ) from e
            else:
                if not service_success:
                    raise RuntimeError(f"{service_name} startup returned False after running.")
                self.log(f"{service_name} started up successfully.")
        
        self.post_message(self.ServicesStarted())

    @on(Worker.StateChanged)
    def _worker_state_changed(self, event: Worker.StateChanged) -> None:

        worker = event.worker  #                          type: ignore[unused-ignore]
        worker_id = getattr(worker, "worker_id", None)  # type: ignore[unused-ignore]
        assert worker_id is not None, "Worker must have a worker_id attribute."

        # if worker.state != WorkerState.RUNNING:
        #     # Remove the worker from the actively running workers dict
        #     if worker_id in self.active_workers:
        #         del self._active_workers[worker_id]

        if worker.state == WorkerState.RUNNING:
            if worker_id not in self.active_workers:
                self.log(Text.from_markup(f"[yellow]Worker {worker.name} is running."))
                self._active_workers[worker_id]["status"] = worker.state

            if not self._worker_check_pending:
                self._worker_check_pending = True
                self.set_timer(3, self._check_running_workers)

        elif worker.state == WorkerState.ERROR:
            self.log.error(
                Text.from_markup(
                    f"[bold red]Worker {worker.name} encountered an error: {worker.error!r}"
                )
            )

            # In the future this should be replaced by a proper error screen.
            # But this will do for now.
            self.notify(
                f"Worker {worker.name} encountered an error: {worker.error!r}",
                severity="error",
                timeout=8,
            )
            del self._active_workers[worker_id]

        elif worker.state == WorkerState.SUCCESS:
            self.log(
                Text.from_markup(f"[bold green]Worker {worker.name} has completed successfully.")
            )

            # Remove the worker from the active workers dict
            worker_id = getattr(worker, "worker_id")  # type: ignore[unused-ignore]
            assert worker_id in self._active_workers
            del self._active_workers[worker_id]

    def _check_running_workers(self) -> None:

        self._worker_check_pending = False
        self.workers_over_limit: dict[str, Worker[Any]] = {}
        at_least_one_from_service_manager = False
        if self.workers:
            log_string = ""

            # When looking over the workers, we only want to look at workers
            # created by TDE and not any built-in Textual workers that might run.
            for worker in self.workers:
                worker_id = getattr(worker, "worker_id", None)
                if worker_id is None:  # this means not from service manager
                    continue

                # Now we know we have a service worker
                at_least_one_from_service_manager = True
                start_time = cast(float, getattr(worker, "start_time"))
                elapsed_time = time() - start_time
                log_string += (
                    f"{worker.name}:\n{worker.state.name} | Elapsed time: {elapsed_time:.2f}\n"
                )

                # And now we can track any over the time limit
                if elapsed_time > 10:
                    self.workers_over_limit[worker_id] = worker

            # This function restarts itself if one of the workers is ours.
            if at_least_one_from_service_manager:
                self.log(
                    Text.from_markup(f"[bold yellow]Worker Status[/bold yellow]\n{log_string}")
                )
                self._worker_check_pending = True
                self.set_timer(3, self._check_running_workers)
            else:
                self.log("No active workers on the Services Manager.")
            return

        # And finally cancel any over the limit
        if self.workers_over_limit:
            for worker in self.workers_over_limit.values():
                self.log.error(f"Worker {worker.name} has exceeded the time limit")
                worker.cancel()
            return

        self.log("No active workers on the Services Manager.")

    async def on_unmount(self) -> None:
        """Unmount the ServicesManager and stop all services."""

        for service_name, service in self._services.__dict__.items():
            if service_name != "logging_service":
                try:
                    service_success = await service.stop()
                except RuntimeError:
                    raise
                except Exception as e:
                    raise RuntimeError(
                        f"{service_name} shutdown failed with an unexpected error: {str(e)}"
                    ) from e
                else:
                    if not service_success:
                        raise RuntimeError(f"{service_name} shutdown returned False after running.")
                    self.log(f"{service_name} stopped successfully.")
        
        # stop logging service last
        try:
            await self.logging_service.stop()
        except Exception as e:
            raise e
