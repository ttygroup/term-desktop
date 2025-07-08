"""windowbase.py"""

from __future__ import annotations
from abc import abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from term_desktop.services.manager import ServicesManager

# Textual imports
# from textual.message import Message

# Textual library imports
from textual_window import Window

# Local imports
from term_desktop.aceofbase import AceOfBase, ProcessContext, ProcessType


class WindowBase(AceOfBase):

    ################
    # ~ CONTRACT ~ #
    ################

    def __init__(self, process_id: str) -> None:
        """The ID is set by the Window service when it initializes the Window process.

        Note that this is not the same as the UID. The UID is a unique identifier
        that is set on all types of processes automatically (anything that inherits from
        a TDE Base class)."""
        self.process_id = process_id

    @abstractmethod
    def get_window(self) -> type[TDEWindow]:
        """
        # ! add note here
        """
        ...

    #####################
    # ~ Backend Setup ~ #
    #####################

    @classmethod
    def validate(cls) -> None:
        cls.validate_stage1()


class TDEWindow(Window):
    """
    Base class for all windows in TDE apps.

    Note that you can't import this and use it apps, this is only for
    direct use by the TDE Window Service.
    """

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

    # NOTE: Windows post an Initialized message automatically,
    # so there's no need to trigger one here like in the other processes.
