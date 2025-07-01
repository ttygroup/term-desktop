from __future__ import annotations
from abc import abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from term_desktop.services.manager import ServicesManager

# Textual imports
from textual.widget import Widget
from textual.message import Message

# Local imports
from term_desktop.aceofbase import AceOfBase, ProcessContext, ProcessType
# from term_desktop.shell.shellmanager import ShellManager

# ? ShellService  →  ShellSession (ABC)  →  ShellLayoutManager


class TDEShellSession(AceOfBase):

    def __init__(self, process_id: str) -> None:
        """The ID is set by the shell service when it initializes the shell session.

        Note that this is not the same as the UID. The UID is a unique identifier
        that is set on all types of processes automatically (anything that inherits from
        a TDE Base class)."""
        self.process_id = process_id

    @abstractmethod
    def get_shell(self) -> TDEShell:
        """build me"""
        ...

    @classmethod
    def validate(cls) -> None:
        super().validate()
        # Additional class-specific validation can be added here.


class TDEShell(Widget):
    """Base class for all shell sessions in TDE. \n

    This is the widget that will be mounted in to the main screen of the app
    when a shell is launched. It provides access to the process context
    and services manager, and allows for posting messages to the app's main content widget. \n

    """

    class Initialized(Message):
        """Posted when the shell is initialized. This will bubble up to
        the main screen, which is attached to the Uber App class."""

        # def __init__(self):
        #     super().__init__()

    def __init__(self, process_context: ProcessContext, **kwargs: Any):
        super().__init__(**kwargs)
        self._process_context = process_context

    @property
    def process_type(self) -> ProcessType:
        return self._process_context["process_type"]

    @property
    def process_id(self) -> str:
        return self._process_context["process_id"]

    @property
    def process_uid(self) -> str:
        return self._process_context["process_uid"]

    @property
    def services(self) -> ServicesManager:
        return self._process_context["services"]

    def post_initialized(self) -> None:
        """This method is called by the WindowService when the window is mounted.
        It is used to post the Initialized message to the app's main content widget.

        This message can be listened to by a TDEapp's main content widget
        to perform any additional setup after the window is mounted and ready to go. \n
        """
        self.post_message(self.Initialized())
        # This is where you can do any additional setup after the window is mounted.
