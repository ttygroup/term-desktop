from __future__ import annotations
from abc import abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager

    # from term_desktop.app_sdk import AppContext
    # from textual.window import Window

# Textual imports
from textual.screen import Screen
from textual.message import Message

# from textual.window import Window

# Local imports
from term_desktop.aceofbase import AceOfBase, ProcessContext, ProcessType


class TDEScreenBase(AceOfBase):
    """Base class for screens in TDE apps."""

    ################
    # ~ CONTRACT ~ #
    ################

    SCREEN_ID: str | None = None

    def __init__(self, process_id: str) -> None:
        """The ID is set by the screen service when it initializes the screen process.

        Note that this is not the same as the UID. The UID is a unique identifier
        that is set on all types of processes automatically (anything that inherits from
        a TDE Base class)."""
        self.process_id = process_id

    @abstractmethod
    def get_screen(self) -> type[TDEScreen]:
        """
        #! ADD NOTE HERE
        """
        ...

    @classmethod
    def validate(cls) -> None:

        required_members = {
            "SCREEN_ID": "class attribute",
            # more will go here as needed
        }
        cls.validate_stage1()
        cls.validate_stage2(required_members)


class TDEScreen(Screen[None]):
    """Base class for screens in TDE apps. \n

    Screens must inherit from this class to be accepted by the screen service.

    Note that this is for full-screen applications intended to be used with
    the TDEScreenBase class above. So far this is intended to be used for
    2 things:
    - Application screens that have a full-screen mode.
    - Built in screens that are used by TDE itself, such as the main screen,
      boot screen, and so on.

    Sometimes apps, widgets, or other screens may want to push smaller
    sreens themselves. Often for things like dialogs and popups.
    It wouldn't really be practical at the moment to try to enforce a contract
    on every single one of those, so this is not a requirement just to push
    a screen in general. How enforced this is will be subject to change in the future.
    """

    class Initialized(Message):
        """Posted when the screen is initialized."""

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
        """This method is called by the ScreenService when the screen is mounted.
        It is used to post the Initialized message to the screen.

        This message can be listened to by a screen to perform any additional
        setup after the screen is mounted and ready to go. \n
        """
        self.post_message(self.Initialized())
