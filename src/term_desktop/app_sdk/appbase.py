"""Base class for all apps. \n"""

# Python imports
from __future__ import annotations
from typing import TypedDict, Any, Callable
from abc import ABC, abstractmethod
from enum import Enum

# Textual imports
from textual.message import Message
from textual.widget import Widget

# Textual library imports
from textual_window.window import STARTING_HORIZONTAL, STARTING_VERTICAL, MODE


class LaunchMode(Enum):
    WINDOW = "window"  # Launch in a new window
    TAB = "tab"  # Launch in a new tab (must implement tabs protocol)
    FULLSCREEN = "fullscreen"  # Launch in fullscreen mode
    DAEMON = "daemon"  # Launch as a background daemon process


class CustomWindowSettings(TypedDict, total=False):
    # width: int
    # height: int
    mode: MODE
    icon: str | None
    classes: str | None
    starting_horizontal: STARTING_HORIZONTAL
    starting_vertical: STARTING_VERTICAL
    start_open: bool
    start_snapped: bool
    allow_resize: bool
    allow_maximize: bool
    menu_options: dict[str, Callable[..., Any]] | None
    animated: bool
    show_title: bool

class DefaultWindowSettings(TypedDict, total=True):
    # width: int
    # height: int
    mode: MODE
    icon: str | None
    classes: str | None
    starting_horizontal: STARTING_HORIZONTAL
    starting_vertical: STARTING_VERTICAL
    start_open: bool
    start_snapped: bool
    allow_resize: bool
    allow_maximize: bool
    menu_options: dict[str, Callable[..., Any]] | None
    animated: bool
    show_title: bool



#! I am still not sure it is gonna work for this to be an ABC.
# * might need to use Textual workers or send messages.
# Can possibly use self.tde tho? Will have to test.
class TDEApp(ABC):

    ################
    # ~ CONTRACT ~ #
    ################

    # Everything in this section must be overridden in the child class.

    APP_NAME: str | None = None
    APP_ID: str | None = None
    ICON: str = "❓"  #         should possibly just be '?'
    DESCRIPTION: str = ""

    @staticmethod
    @abstractmethod
    def launch_mode() -> LaunchMode:
        """Returns the launch mode for the app. \n

        Must return one of the `LaunchMode` enum values.
        """
        raise NotImplementedError("Subclasses must implement the launch_mode @staticmethod.")

    @staticmethod
    @abstractmethod
    def main_content() -> Widget | None:
        """Returns the class definiton for the main content widget for the app. \n

        If the TDEapp is a normal app (runs in a window or full screen), this must return
        the main content Widget for your app.

        If the TDEapp is a daemon, this method must return None.
        """
        raise NotImplementedError("Subclasses must implement the main_content @staticmethod.")

    @classmethod
    def custom_window_settings(cls) -> CustomWindowSettings:
        """Returns the settings for the window to be created. \n

        This method can be optionally overridden to provide custom window settings.
        """
        return {
            # This returns an empty dictionary when not overridden.

            # "start_open": True,
            # "mode": "permanent",  # default is temporary
            # "icon": "custom icon",
            # "allow_resize": False,
            # etc etc
            # See CustomWindowSettings
        }

    #####################
    # ~ Base Messages ~ #
    #####################

    class StartApp(Message):
        """Posted when an app is either started or restarted."""

        def __init__(self, app: TDEApp):
            super().__init__()
            self.app = app

    #####################
    # ~ Backend Setup ~ #
    #####################

    @classmethod
    def _loader(cls) -> type[TDEApp]:
        return cls

    def __init__(self, id: str, tde: TDEApp) -> None:
        self.id = id
        self.tde = tde

        #! Create process manager appending process
        # self.tde.processes.append(self)
        # self.tde.on_app_launched(self.__class__)
        # self.instance_number = instance_number  #! this shouldnt matter. Process manager.

    def __init_subclass__(cls) -> None:
        """Additional Validation above what the ABC can provide."""

        required_members = {
            "APP_NAME": "class attribute",
            "APP_ID": "class attribute",
            # more will go here as needed
        }

        for attr_name, kind in required_members.items():

            try:
                attr = getattr(cls, attr_name)
            except AttributeError:
                raise NotImplementedError(f"{cls.__name__} must implement {attr_name} ({kind}).")
            else:
                if attr is None:
                    raise NotImplementedError(f"{cls.__name__} must implement {attr_name} ({kind}).")

    async def kill(self) -> None:

        pass
        # self.tde.processes.remove(self)
        # self.tde.on_app_killed(self.__class__)

    @classmethod
    def default_window_settings(cls) -> DefaultWindowSettings:
        """Returns the settings for the window to be created. \n

        This method can be optionally overridden to provide custom window settings.
        """
        return {
            # "width": 45,      # ! not sure width and height should be here
            # "height": 20,
            "mode": "temporary",
            "icon": cls.ICON,
            "classes": None,
            "starting_horizontal":  "center",
            "starting_vertical": "middle",
            "start_open": False,
            "start_snapped": True,
            "allow_resize": True,
            "allow_maximize": False,
            "menu_options": None,
            "animated": True,
            "show_title": True
        }