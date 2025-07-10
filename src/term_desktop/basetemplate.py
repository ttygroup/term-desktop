"""basetemplate.py

Currently there are five base types in TDE:
- AppBase
- ServiceBase
- ScreenBase
- ShellBase
- WindowBase

Everything that inherits from a base is considered a "process" and thus is given
a UID and can be managed/logged in a central location.

In the future we may want to add more types. This template will help
to streamline the creation of new base classes."""

from __future__ import annotations
from abc import abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from term_desktop.services.serviceesmanager import ServicesManager

# Textual imports
from textual.widget import Widget
from textual.message import Message

# Local imports
from term_desktop.aceofbase import AceOfBase, ProcessContext, ProcessType


class FooBase(AceOfBase):

    ################
    # ~ CONTRACT ~ #
    ################

    FOO_ID: str | None = None

    def __init__(self, process_id: str) -> None:
        """The ID is set by the Foo service when it initializes the Foo process.

        Note that this is not the same as the UID. The UID is a unique identifier
        that is set on all types of processes automatically (anything that inherits from
        a TDE Base class)."""
        self.process_id = process_id

    @abstractmethod
    def get_foo(self) -> type[TDEWidgetFoo]:  # returning the definition, not an instance
        """
        build me
        """
        ...

    #####################
    # ~ Backend Setup ~ #
    #####################

    @classmethod
    def validate(cls) -> None:
        cls.validate()

        # You can also add class level attributes that must be
        # implemented by subclasses:

        # required_members = {
        #     "FOO_NAME": "class attribute",
        #     "FOO_ID": "class attribute",
        # }
        # cls.validate_stage2(required_members)


class TDEWidgetFoo(Widget):
    """
    Base class for all widgets of Foo type in TDE.
    """

    class Initialized(Message):
        """Posted when the TDEWidgetFoo is initialized."""

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
        """This method is called by the FooService when the WidgetFoo is mounted.
        It is used to post the Initialized message to the WidgetFoo when the service
        has decided that it is complete.

        This message can be listened to by a WidgetFoo to perform any additional
        setup after the WidgetFoo is mounted and ready to go. \n
        """
        self.post_message(self.Initialized())
