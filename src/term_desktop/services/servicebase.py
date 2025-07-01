from __future__ import annotations
from abc import abstractmethod
from functools import partial
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from term_desktop.services.manager import ServicesManager
    from textual.worker import Worker
    from textual.message import Message

# Local imports
from term_desktop.aceofbase import AceOfBase

# NOTE: services don't require a context dictionary.
# The service manager is just attached directly. They can afford to be a bit
# more tightly coupled compared to other components like apps, screens, or shells.


class TDEServiceBase(AceOfBase):

    def __init__(self, services_manager: ServicesManager) -> None:
        self.services_manager = services_manager

    @classmethod
    def validate(cls) -> None:
        super().validate()
        # Additional class-specific validation can be added here.

    @abstractmethod
    async def start(self) -> bool: ...

    @abstractmethod
    async def stop(self) -> bool:
        # cleanup
        ...

    ######################
    # ~ Bridge Methods ~ #
    ######################
    # These are all methods that bridge to a corresponding method on the
    # services manager. Since base classes are not Textual objects, they do not have
    # access to textual abilities like run worker, post message, or log to console.
    # Futhermore, since all service workers run on the service manager class, that
    # might make it easier to monitor or control them in the future

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
        self.log.debug(f"Running worker: {name} in group: {group}")
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

    def post_message(self, message: Message) -> None:
        """
        Post a message to the services manager. This will bubble up to
        the main App class.
        """
        self.services_manager.post_message(message)
