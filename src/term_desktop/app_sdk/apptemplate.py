"""Template file for creating a new TDE app.

This bare-bones template provides a starting point for creating a new app
using the Term Desktop Environment (TDE) app SDK. It includes a basic
content widget and the necessary methods to define the app's behavior
and settings.

#! more instructions here on how to use it, link to the SDK docs, etc.
"""

# Python imports
from __future__ import annotations

# Textual imports
from textual.widgets import Static

# Unused Textual imports (for reference):
from textual import events, on
# from textual.message import Message
# from textual.binding import Binding

# Textual library imports
from textual_window.window import WindowStylesDict

# Local imports
from term_desktop.app_sdk import (
    TDEApp,
    TDEMainWidget,
    LaunchMode,
    CustomWindowSettings,
    CustomWindowMounts,
)


class TemplateContent(TDEMainWidget):

    DEFAULT_CSS = """
    #my_static { border: solid red; }
    """
    # BINDINGS = []

    def compose(self):

        yield Static("Your app content goes here", id="my_static")

    @on(TDEMainWidget.Initialized)
    def post_initialization(self, event: TDEMainWidget.Initialized) -> None:
        """
        This event is posted when the main widget's window is fully initialized.
        You can perform any setup or post-initialization here.
        """
        # You can access the current window through this event:
        current_window = event.window

        # You can also access the active window using the process ID.
        # The process_id is available as self.process_id, which is set by the process manager.
        # To get the window by current process ID:
        current_window = self.services.window_service.get_window_by_process_id(self.process_id)

    @on(events.DescendantFocus)
    def descendant_focused(self, event: events.DescendantFocus) -> None:
        
        # This is an example of how you can use the DescendantFocus and DescendantBlur events
        # which are sent by any child widgets inside of the main widget.
        # This is useful if you want to do something like modify something on the
        # main widget or the window (ie change colors, styles, etc) when a child widget
        # inside of the main widget gets focused or blurred.
        pass

    @on(events.DescendantBlur)
    def descendant_blurred(self, event: events.DescendantBlur) -> None:
        pass

class Template(TDEApp):

    APP_NAME: str | None = None
    APP_ID: str | None = None
    ICON: str = "❓"  #         should possibly just be '?'
    DESCRIPTION: str = "Your Description Here"

    def launch_mode(self) -> LaunchMode:
        """Returns the launch mode for the app. \n

        Must return one of the `LaunchMode` enum values.
        """
        return LaunchMode.WINDOW  # or FULLSCREEN, or DAEMON

    def get_main_content(self) -> type[TDEMainWidget] | None:
        """Returns the class definiton for the main content widget for the app. \n
        Must return a definition of a Widget subclass, not an instance of it.

        If the TDEapp is a normal app (runs in a window or full screen), this must return
        the main content Widget for your app. If the TDEapp is a daemon, this method must
        return None.
        """
        # Notice what we're returning is the defintion of the above
        # TemplateContent class. Do not instantiate it.
        return TemplateContent

    def custom_window_settings(self) -> CustomWindowSettings:
        """Returns the settings for the window to be created. \n

        This is not part of the contract and not necessary to implement.
        This method can be optionally implemented to provide custom window settings.
        """
        return {
            # This returns an empty dictionary when not overridden.
            # "start_open": False,  #       default is True
            # "allow_resize": False,  #     default is True
            # "allow_maximize": False,  #   default is True
            # see CustomWindowSettings for more options
        }

    def custom_window_mounts(self) -> CustomWindowMounts:
        """Returns a dictionary of custom mounts to be added to the window. \n

        This method can be optionally overridden to provide custom mounts for the window.
        """
        return {
            # This returns an empty dictionary when not overridden.
            # "above_topbar": None,
            # "below_topbar": None,
            # "left_pane": None,
            # "right_pane": None,
            # "above_bottombar": None,
            # "below_bottombar": None,
        }

    def window_styles(self) -> WindowStylesDict:
        """Returns a dictionary of styles to be applied to the window. \n

        Note that although you can set styles within your own widget (app) all you want
        using the `CSS` class variable as described above and in the SDK (doesn't exist yet),
        you cannot set styles for the window itself.
        Window instances are created and handled by TDE's Window Service. In order to
        set styles for the window itself, you must put them in the dictionary
        returned by this method. \n

        Provide your custom styles for the window.
        This dictionary is passed into the `styles_dict` parameter of the Window class
        constructor in the Textual-Window library. It's the same as the `styles_dict`
        would be used in the library if it was imported into a regular Textual app.

        This dictionary is quite bare-bones at the moment, but it can be expanded
        in the future to accept more styles as needed. \n
        """
        # These settings shown reflect the same default settings that are used
        # by the Textual-Window library for a Window instance. You could see these same
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
