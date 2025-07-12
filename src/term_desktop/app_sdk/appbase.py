"""Base class for all apps. \n"""

# Python imports
from __future__ import annotations
from typing import TypedDict, Any, Callable, TYPE_CHECKING
from abc import abstractmethod
from enum import Enum

if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager
    from term_desktop.services.windows import WindowService
    from term_desktop.services.screens import ScreenService    
    from textual_window.window import (
        Window,
        STARTING_HORIZONTAL,
        STARTING_VERTICAL,
        MODE,
        WindowStylesDict,
    )

# Textual imports
from textual.message import Message
from textual.widget import Widget

# Local imports
from term_desktop.aceofbase import AceOfBase, ProcessContext, ProcessType


class LaunchMode(Enum):
    WINDOW = "window"  #            Launch in a new window
    FULLSCREEN = "fullscreen"  #    Launch in fullscreen mode
    DAEMON = "daemon"  #            Launch as a background daemon process


class CustomWindowSettings(TypedDict, total=False):
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
    name: str | None  #  This is the app name, not the window name.
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


class CustomWindowMounts(TypedDict, total=False):
    """A dictionary of custom mounts to be added to the window.
    You can attach one widget to each of the following keys."""

    above_topbar: type[Widget]  #      mounted above the top bar.
    below_topbar: type[Widget]  #      mounted below the top bar
    left_pane: type[Widget]  #         mounted to the left of the content area
    right_pane: type[Widget]  #        mounted to the right of the content area
    above_bottombar: type[Widget]  #   mounted above the bottom bar
    below_bottombar: type[Widget]  #   mounted below the bottom bar


class TDEAppBase(AceOfBase):

    ################
    # ~ CONTRACT ~ #
    ################

    APP_NAME: str | None = None
    APP_ID: str | None = None
    APP_AUTHOR: str | None = None

    @abstractmethod
    def launch_mode(self) -> LaunchMode:
        """Returns the launch mode for the app.

        Must return one of the `LaunchMode` enum values.
        """
        raise NotImplementedError("Subclasses must implement the launch_mode @staticmethod.")

    @abstractmethod
    def get_main_content(self) -> type[TDEMainWidget] | None:
        """Returns the class definiton for the main content widget for the app.
        Must return a definition of a Widget subclass, not an instance of it.

        If the TDEapp is a normal app (runs in a window or full screen), this must return
        the main content Widget for your app. If the TDEapp is a daemon, this method must
        return None.

        #! SUPPORT FOR FULLSCREEN AND DAEMON APPS IS NOT YET IMPLEMENTED.
        """
        raise NotImplementedError("Subclasses must implement the main_content @staticmethod.")

    @abstractmethod
    def window_styles(self) -> WindowStylesDict:
        """Returns a dictionary of styles to be applied to the window.

        Note that although you can set styles within your own main content widget (app)
        using the `CSS` class variable as described above and in the SDK (doesn't exist yet),
        you cannot set styles for the window itself.
        Window instances are created and handled by TDE's Window Service. In order to
        set styles for the window itself, you must put them in the dictionary
        returned by this method.

        Provide your custom styles for the window.
        This dictionary is passed into the `styles_dict` parameter of the Window class
        constructor in the Textual-Window library. It's the same as the `styles_dict`
        would be used in the library if it was imported into a regular Textual app.

        This dictionary is quite bare-bones at the moment, but it can be expanded
        in the future to accept more styles as needed.
        """
        # These settings shown reflect the same default settings that are used
        # by the Textual-Window library for a Window instance. You can see these same
        # settings in the DEFAULT_CSS class variable in the Window class.

        # This returns an empty dictionary when not overridden.
        return {
            #     "width": 25,  #
            #     "height": 12,  #
            #     "max_width": None,  #  default is 'size of the parent container'
            #     "max_height": None,  # default is 'size of the parent container'
            #     "min_width": 12,  #
            #     "min_height": 6,  #
        }

    ##########################
    # ~ OPTIONAL OVERRIDES ~ #
    ##########################

    ICON: str = "❓"  #         should possibly just be '?'
    DESCRIPTION: str = ""

    def custom_window_settings(self) -> CustomWindowSettings:
        """Returns the settings for the window to be created.

        This method can be optionally overridden to provide custom window settings.
        """
        # This returns an empty dictionary when not overridden.
        return {
            # "start_open": True,
            # "mode": "permanent",  # default is temporary
            # "icon": "custom icon",
            # "allow_resize": False,
            # etc etc
            # See CustomWindowSettings
        }

    def custom_window_mounts(self) -> CustomWindowMounts:
        """Returns a dictionary of custom mounts to be added to the window.

        This method can be optionally overridden to provide custom mounts for the window.
        """
        # This returns an empty dictionary when not overridden.
        return {
            # "above_topbar": None,
            # "below_topbar": None,
            # "left_pane": None,
            # "right_pane": None,
            # "above_bottombar": None,
            # "below_bottombar": None,
        }

    #####################
    # ~ Base Messages ~ #
    #####################

    class AppStarted(Message):
        """Posted when an app is either started or restarted."""

        def __init__(self, app: TDEAppBase):
            super().__init__()
            self.app = app

    #####################
    # ~ Backend Setup ~ #
    #####################

    def __init__(self, process_id: str) -> None:
        """The ID is set by the process service when it initializes the app process.
        It will append a number to keep track of multiple instances of the same app.

        Note that this is not the same as window number - A single app process instance
        can still hypothetically have multiple windows managed by it.
        It is also not the same as the UID. The UID is a unique identifier
        that is set on all types of processes automatically (anything that inherits from
        a TDE Base class)."""
        self.process_id = process_id

    async def kill(self) -> None:
        # N/I yet
        pass

    @classmethod
    def validate(cls) -> None:
        """Run by the App Service to validate that apps meet the contract.

        APP_ID and APP_NAME are required to even register the app. If they are not set,
        the app won't even show up in the start menu / loader service.

        After that, if any of the abstract methods are not implemented,
        the class will be marked as BROKEN and MISSING_METHODS will contain the set of
        missing abstract methods.
        This is used by the App service to determine if the app can be launched or not
        and to provide feedback to the user in the start menu / app loader screen.

        If the app is broken, it will still be registered and shown in the start menu,
        but with a warning that it cannot be launched. We can then easily expand that
        to add more information that the user could click on to see what is missing.
        """
        required_members = {
            "APP_NAME": "class attribute",
            "APP_ID": "class attribute",
            "APP_AUTHOR": "class attribute",
            # more will go here as needed
        }
        cls.validate_stage1()
        cls.validate_stage2(required_members)

    @property
    def default_window_settings(cls) -> DefaultWindowSettings:
        """Returns the settings for the window to be created. \n

        If you want to change any of these defaults, don't override this method, instead
        override the `get_custom_window_settings` method.

        These settings mirror the default settings that are used by the
        Textual-Window library for a Window instance, aside for the
        name and icon which are set to the app name and icon respectively.
        """
        return {
            "name": cls.APP_NAME,
            "mode": "temporary",
            "icon": cls.ICON,
            "classes": None,
            "starting_horizontal": "center",
            "starting_vertical": "middle",
            "start_open": True,
            "start_snapped": True,
            "allow_resize": True,
            "allow_maximize": True,
            "menu_options": None,
            "animated": True,
            "show_title": True,
        }


class TDEMainWidget(Widget):
    """Base class for all main content widgets in TDE apps.

    This is the widget that will be mounted in the window when the app is launched.
    Any Textual apps being converted into TDE apps should consider
    this as being the equivalent of the main App class.

    #! NOTE: NOT FOR SCREENS, STILL NEED TO BUILD SUPPORT FOR THEM.

    The app_context is passed in by the Process Manager when it initializes the app.
    """

    class Initialized(Message):
        """Posted when the main content widget is initialized."""

        def __init__(self, window: Window):
            super().__init__()
            self.window = window

    def __init__(self, process_context: ProcessContext):
        """The process context is passed in by the Process Manager when it initializes the app.
        It contains the process type, process ID, process UID, and services manager.

        If you override this method, you must have an argument named `process_context`
        which you pass into the super constructor:
        ```
        super().__init__(process_context=process_context, **kwargs)
        ```"""
        super().__init__()
        self._process_context = process_context
        self._window_process_id: str | None = None  # only if window used
        self._screen_process_id: str | None = None  # only if screen used

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

    @property
    def window_process_id(self) -> str | None:
        """Returns the process ID of the window that this widget is mounted in.
        This is only set if the widget is mounted in a window."""
        return self._window_process_id

    def set_window_process_id(self, value: str | None, caller: WindowService) -> None:
        """Attaches the process ID of the window that this widget is mounted in.
        This is only set if the widget is mounted in a window."""

        if caller is not self.services.window_service:
            raise TypeError("This can only be set by the WindowService.")
        self._window_process_id = value

    #! NOT USED YET - SCREEN SYSTEM FOR APPS NOT BUILT YET
    @property
    def screen_process_id(self) -> str | None:
        """Returns the process ID of the screen that this widget is mounted in.
        This is only set if the widget is mounted in a screen."""
        return self._screen_process_id

    def set_screen_process_id(self, value: str | None, caller: ScreenService) -> None:
        """Attaches the process ID of the screen that this widget is mounted in.
        This is only set if the widget is mounted in a screen."""

        if caller is not self.services.screen_service:
            raise TypeError("This can only be set by the ScreenService.")
        self._screen_process_id = value

    def post_initialized(self, window: Window) -> None:
        """This method is called by the WindowService when the window is mounted.
        It is used to post the Initialized message to the app's main content widget.

        This message can be listened to by a TDEapp's main content widget
        to perform any additional setup after the window is mounted and ready to go.
        """
        self.post_message(self.Initialized(window))
        # This is where you can do any additional setup after the window is mounted.
