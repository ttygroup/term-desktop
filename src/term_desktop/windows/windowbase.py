"""windowbase.py"""

from __future__ import annotations

# from abc import abstractmethod
from typing import TYPE_CHECKING  # , Any

if TYPE_CHECKING:
    from textual.widget import Widget
    from textual_window.window import WindowStylesDict
    from term_desktop.services.servicesmanager import ServicesManager
    from term_desktop.app_sdk.appbase import DefaultWindowSettings

# Textual imports
# from textual.message import Message

# Textual library imports
from textual_window import Window

# Local imports
from term_desktop.aceofbase import AceOfBase, ProcessContext, ProcessType


class TDEWindowBase(AceOfBase):

    # NOTE: Nothing inherits from this class. It's just used to identify the
    # window process in a manner that's consistent with the rest of TDE.

    def __init__(
        self,
        app_process_id: str,
        window_process_id: str,
        instance_num: int,
    ) -> None:
        """window_process_id is set by the Window service when it initializes the Window process.

        Note that this is not the same as the UID. The UID is a unique identifier
        that is set on all types of processes automatically (anything that inherits from
        a TDE Base class)."""
        self.WINDOW_ID = f"{app_process_id}-window"

        self.app_process_id = app_process_id
        self.window_process_id = window_process_id
        self.instance_num = instance_num

    def get_window(self) -> type[TDEWindow]:
        """
        # ! add note here
        """
        return TDEWindow

    @classmethod
    def validate(cls) -> None:
        cls.validate_stage1()


class TDEWindow(Window):
    """
    Base class for all windows in TDE apps.

    Note that you can't import this and use it apps, this is only for
    direct use by the TDE Window Service.

    Args:
        content_instance (Widget): The content widget for the window.
        styles_dict (WindowStylesDict): Styles dictionary for the window.
        process_context (ProcessContext): Context containing process information.
        window_id (str): Unique identifier for the window.
        window_dict (DefaultWindowSettings): Dictionary containing default window settings.
    """

    # This is a wrapper around the Window class from the textual-window library.
    # We don't want apps or processes to be able to try to make or mount their own
    # windows directly.

    def __init__(
        self,
        content_instance: Widget,
        styles_dict: WindowStylesDict,
        process_context: ProcessContext,
        window_id: str,
        window_dict: DefaultWindowSettings,
    ):
        super().__init__(
            content_instance,
            id=window_id,
            styles_dict=styles_dict,
            **window_dict,
        )
        self._process_context = process_context
        self._window_id = window_id

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
    def window_process_id(self) -> str:
        return self._window_id

    @property
    def services(self) -> ServicesManager:
        return self._process_context["services"]

    # NOTE: Windows post an Initialized message automatically,
    # so there's no need to trigger one here like in the other processes.
