from __future__ import annotations
from abc import ABC, abstractmethod
# from typing import TYPE_CHECKING #, Any, Callable
# if TYPE_CHECKING:
    # from term_desktop.services.servicesmanager import ServicesManager
    # from textual.worker import Worker  

# from textual import log

# ShellService  →  spawns →  ShellSession (ABC)  →  mounts →  ShellLayoutManager (widget tree)


class ShellSession(ABC):

    @abstractmethod
    def get_layout(self) -> ShellLayoutManager:
        """Returns the main shell layout widget to mount on screen."""

    @abstractmethod
    def session_id(self) -> str:
        """Returns a unique identifier for this shell session."""

    def on_enter(self) -> None:
        """Called when this shell session becomes active."""
    
    def on_exit(self) -> None:
        """Called before this session is replaced or terminated."""
