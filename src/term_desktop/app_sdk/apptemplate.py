"""Template file for creating a new TDE app.

This bare-bones template provides a starting point for creating a new app
using the Term Desktop Environment (TDE) app SDK. It includes a basic
content widget and the necessary methods to define the app's behavior
and settings.

#! more instructions here on how to use it
"""

# Python imports
from __future__ import annotations

# Textual imports
from textual import events, on
from textual.widgets import Static

# from textual.message import Message
# from textual.binding import Binding
from textual.widget import Widget

from term_desktop.app_sdk.appbase import (
    TDEApp,
    LaunchMode,
    CustomWindowSettings,
    CustomWindowMounts,
)


class TemplateContent(Widget):

    DEFAULT_CSS = """
    TemplateContent {
        & > #my_static { border: solid red; }
    }    
    """
    # BINDINGS = []

    def compose(self):

        yield Static("Your app content goes here", id="my_static")

    @on(events.Focus)
    def on_mount(self) -> None:
        # Here you can set which widgets inside the window you would like to gain focus
        # when the window is mounted or focused.
        self.query_one("#my_static", Static).focus()

    # The mount and focus methods can be split into two methods if you prefer:
    # def on_focus(self) -> None:
    #     self.query_one("#my_static", Static).focus()


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

    def get_main_content(self) -> type[Widget] | None:
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

        return {
            # This returns an empty dictionary when not overridden.
            # "above_topbar": None,
            # "below_topbar": None,
            # "left_pane": None,
            # "right_pane": None,
            # "above_bottombar": None,
            # "below_bottombar": None,
        }
