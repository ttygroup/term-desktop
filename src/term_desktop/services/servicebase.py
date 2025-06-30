from __future__ import annotations
from abc import ABC, abstractmethod
from functools import partial
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager
    from textual.worker import Worker  

from textual import log


class BaseService(ABC):

    def __init__(self, services_manager: ServicesManager) -> None:
        self.services_manager = services_manager

    # Just start and stop at the moment.
    # Lots of room for expansion.

    @abstractmethod
    async def start(self) -> bool: ...

    @abstractmethod
    async def stop(self) -> bool:
        # cleanup
        ...

    def run_worker(
            self, 
            work: Callable[..., Any],
            *args: Any,
            name: str | None = "",
            group: str = "services",
            description: str = "",
            exit_on_error: bool = True,
            start: bool = True,
            exclusive: bool = False,
            thread: bool = True,
            **kwargs: Any,                      
        ) -> Worker[Any]:
        """
        Run a worker function in the services manager.  
        
        Positional and keyword arguments are passed to the worker function.

        Note that this is a bridge function to the actual `run_worker` method
        of the `ServicesManager`. Services are not Textual objects and are not
        able to run workers themselves.
        
        Returns:
            Worker[Any]: The worker instance that was started.
        """
        log.debug(f"Running worker: {name} in group: {group}")
        partial_func = partial(work, *args, **kwargs)
        worker = self.services_manager.run_worker(
            work=partial_func,
            name=name,
            group=group,
            description=description,
            exit_on_error=exit_on_error,
            start=start,
            exclusive=exclusive,
            thread=thread,
        )
        return worker