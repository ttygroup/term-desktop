"""
syslogs.py
"""

# Python imports
from __future__ import annotations
import logging
import time

# import inspect

# from typing import Any, Type
# import os
# import sys
# import platform

# Textual imports
# import rich.repr
from textual.app import ComposeResult
from textual.widgets import DataTable #, Static
# from textual.containers import Container
from rich.text import Text

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
# from term_desktop.services.tde_logging import LogPayload


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
            "starting_horizontal": "right",  # default is "center"
            # "start_open": False,  #       default is True
            # "allow_resize": False,  #     default is True
            # "allow_maximize": False,  #   default is True
            # see CustomWindowSettings for more options
        }

    def window_styles(self) -> WindowStylesDict:

        return {
            "width": 87,
            "height": 30,
        }


class SysLogsWidget(TDEMainWidget):

    DEFAULT_CSS = """
    #menubar_placeholder { width: 1fr; height: 1; }
    """

    def compose(self) -> ComposeResult:

        self.initialized = False
        self.counter = 0
        yield DataTable(
            id="log_viewer_table",
            zebra_stripes=True,
            cursor_type="row",
        )

    def on_mount(self) -> None:

        table: DataTable[str | Text] = self.query_one("#log_viewer_table", DataTable)
        self.index_key = table.add_column(" ", key="index")        
        table.add_column("Message", key="message", width=60)
        table.add_column("Group", key="level")
        table.add_column("Path", key="path")
        table.add_column("Line", key="line_number")
        table.add_column("Time", key="created")
        table.add_column("Session ID", key="session_id") 
        
        log_memory = self.services.logging_service.memory_buffer

        # write out the memory buffer to the log viewer
        for record in log_memory:
            self.handle_new_log(record)

        # subscribe to new log records
        self.services.logging_service.subscribe_to_signal(self.handle_new_log)
        
        table.scroll_end()
        self.initialized = True


    def handle_new_log(self, log_record: logging.LogRecord) -> None:
        
        table: DataTable[str | Text] = self.query_one("#log_viewer_table", DataTable)
        row_key = table.add_row(
            str(self.counter),
            Text(str(log_record.msg), overflow="fold"),
            str(log_record.__dict__.get("group")),
            Text(str(log_record.__dict__.get("path")), overflow="fold"),
            str(log_record.__dict__.get("line_number")),
            time.strftime("%H:%M:%S", time.localtime(log_record.__dict__.get("timestamp"))),
            str(log_record.__dict__.get("session_id")),
        )
        # self.counter += 1
        row_index = table.get_row_index(row_key)
        table.update_cell(row_key, self.index_key, str(row_index))
        if self.initialized:
            table.scroll_end()
                        
        # name=tde_logger                                                                                                                     ▊
        # msg=RichLog(id='log_viewer') was focused                                                                                            ▊
        # args=()                                                                                                                             ▊
        # levelname=DEBUG                                                                                                                     ▊
        # levelno=10                                                                                                                          ▊
        # pathname=/home/brent/vscode-projects/term-desktop/src/term_desktop/services/tde_logging.py                                          ▊
        # filename=tde_logging.py                                                                                                             ▊
        # module=tde_logging                                                                                                                  ▊
        # exc_info=None                                                                                                                       ▊
        # exc_text=None                                                                                                                       ▊
        # stack_info=None                                                                                                                     ▊
        # lineno=154                                                                                                                          ▊
        # funcName=log                                                                                                                        ▊
        # created=1756861622.4891434                                                                                                          ▊
        # msecs=489.0                                                                                                                         ▊
        # relativeCreated=8955812.801361084                                                                                                   ▊
        # thread=139809355833472                                                                                                              ▊
        # threadName=MainThread                                                                                                               ▊
        # processName=MainProcess                                                                                                             ▊
        # process=60827                                                                                                                       ▊
        # taskName=Task-1                                                                                                                     ▊
        # session_id=139809345227616                                                                                                          ▊
        # group=DEBUG                                                                                                                         ▊
        # path=/home/brent/vscode-projects/term-desktop/.venv/lib/python3.12/site-packages/textual/screen.py                                  ▊
        # line_number=1042                                                                                                                    ▊
        # message=RichLog(id='log_viewer') was focused
        

    def on_unmount(self) -> None:
        # unsubscribe from log records
        self.services.logging_service.unsubscribe_from_signal(self.handle_new_log)
