"""
syslogs.py
"""

# Python imports
from __future__ import annotations

# from typing import Any, Type
# import os
# import sys
# import platform

# Textual imports
from textual.app import ComposeResult
from textual.widgets import RichLog  # , Static

# Unused Textual imports (for reference):
# from textual import events, on
# from textual.message import Message
# from textual.binding import Binding

# Textual library imports
from textual_window.window import WindowStylesDict

# Local imports
from term_desktop.app_sdk import (
    TDEAppBase,
    TDEMainWidget,
    LaunchMode,
    CustomWindowSettings,
)
from term_desktop.services.tde_logging import LogPayload


class SysLogsMeta(TDEAppBase):

    APP_NAME = "System Logs"
    APP_ID = "syslogs"
    ICON = "📝"
    DESCRIPTION = "View system logs."
    APP_AUTHOR = "TDE Team"

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
        return SysLogsWidget

    def custom_window_settings(self) -> CustomWindowSettings:
        """Returns the settings for the window to be created. \n

        This is not part of the contract and not necessary to implement.
        This method can be optionally implemented to provide custom window settings.
        """
        return {
            # This returns an empty dictionary when not overridden.
            # see CustomWindowSettings for more options
        }

    def window_styles(self) -> WindowStylesDict:

        return {
            "width": 60,  #
            "height": 30,  #
            # "max_width": None,  #  default is 'size of the parent container'
            # "max_height": None,  # default is 'size of the parent container'
            # "min_width": 12,  #
            # "min_height": 6,  #
        }


class SysLogsWidget(TDEMainWidget):

    # DEFAULT_CSS = """
    # #title { border: solid $primary; }
    # #content { width: auto; height: auto; }
    # """
    
    def compose(self) -> ComposeResult:

        yield RichLog(id="log_viewer")
        
    def on_mount(self):
        log_viewer = self.query_one(RichLog)
        log_memory = self.services.logging_service.memory_buffer
        
        # write out the memory buffer to the log viewer
        for record in log_memory:
            log_viewer.write(record)
            
        # subscribe to new log records
        self.services.logging_service.log_signal.subscribe(self.handle_new_log)
        
    def handle_new_log(self, log_payload: LogPayload) -> None:
        log_viewer = self.query_one(RichLog)
        log_viewer.write(log_payload["msg"])
        
    def on_unmount(self) -> None:
        # unsubscribe from log records
        self.services.logging_service.log_signal.unsubscribe(self.handle_new_log)
