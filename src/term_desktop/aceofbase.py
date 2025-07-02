from __future__ import annotations
from typing import TypedDict, TYPE_CHECKING, Any
from abc import ABC  # , abstractmethod
import enum

if TYPE_CHECKING:
    from term_desktop.services.manager import ServicesManager
    from textual import Logger

from textual import log


class ProcessType(enum.Enum):
    """Enum for different types of processes in TDE."""

    APP = "app"
    SERVICE = "service"
    SCREEN = "screen"
    SHELL = "shell"
    # Add more process types as needed.

class ProcessContext(TypedDict, total=True):
    """
    'Children' that are spawned by a process will always have the
    follow attributes passed in to them as part of their context.

    This allows things like main content widgets, content screens, or shell
    sessions to 1) have access to all services directly through
    self properties, and 2) access their own unique process identifiers
    that is used to track them in the system, if they need to do so.
    """

    process_type: ProcessType
    process_id: str  # Process-level ID, for use by a process's respective service
    process_uid: str  # Unique process identifier at the system level
    services: ServicesManager  # The services manager instance
    # Add more fields as needed.


class AceOfBase(ABC):
    """The Ace Of Base class is the top level ABC that all base classes
    in the app must inherit from.

    Everything in the app that inherits from a base class represents a "process"
    of some kind. At the moment the four types of bases are:
    - App base
    - Service base
    - Screen base
    - Shell base

    In the future this might be expanded to include more bases. By having them all
    inherit from a single ABC, we can more easily centralize things that all TDE
    processes might need to have. A good start is a UID system for giving every single
    process in TDE (including services, screens, etc) a unique identifier.
    """

    BROKEN: bool = False  # Indicates if the app is broken and cannot be launched.
    MISSING_METHODS: frozenset[str] | None = None  # Set of missing abstract methods, if any.

    @property
    def uid(self) -> str:
        """Globally unique ID for this entity."""

        return f"{self.__class__.__name__.lower()}:{id(self)}"

    @property
    def all_that_she_wants(self) -> str:
        "Alias for uid()"
        return self.uid

    @property
    def log(self, *args: Any, **kwargs: Any) -> Logger:
        """
        Log a message using the Textual log system.

        This is a convenience method to use the Textual log system
        directly from any process (Anything using an ABC is not a
        Textual object).
        """
        return log

    @classmethod
    def validate(cls) -> None:
        """High-level validation for the base class.
        Make sure you call `super().validate()` if you override this
        method in a subclass."""

        missing = cls.__abstractmethods__
        if missing:
            cls.BROKEN = True
            cls.MISSING_METHODS = missing
            raise NotImplementedError(
                f"{cls.__name__} is missing the following abstract methods: \n"
                f"{', '.join(missing)}\n"
                "Please implement them to make the screen functional."
            )
