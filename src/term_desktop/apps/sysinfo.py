"""
sysinfo.py
"""

# Python imports
from __future__ import annotations
# from typing import Any, Type
import os
import sys
import platform

# Textual imports
# from textual import events, on
from textual.widgets import Static
# from textual.message import Message
# from textual.binding import Binding
from textual.widget import Widget

from term_desktop.app_sdk.appbase import (TDEApp, LaunchMode, CustomWindowSettings,)


class SysInfoWidget(Widget):

    DEFAULT_CSS = """
    TemplateContent {
        & > #my_static { border: solid red; }
    #title { border: solid $primary; }
    #content { width: auto; height: auto; }        
    }    
    """
    # BINDINGS = []

    def compose(self):

        self.static_system_info = self.get_static_system_info()
        yield Static("System Information", id="title")
        yield Static(
            "\n".join(f"{key}: {value}" for key, value in self.static_system_info.items()),
            id="content",
        ) 

    def get_static_system_info(self) -> dict[str, str]:
        uname = platform.uname()
        if hasattr(os, "sysconf"):
            memory = f"{round(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024. ** 3), 2)} GB"
        else:
            memory = "Unknown"

        return {
            "OS": f"{uname.system} {uname.release}",
            "Freedesktop_os label": str(platform.freedesktop_os_release().get("PRETTY_NAME", "Unknown")),
            "Machine": uname.machine,
            "Architecture": platform.architecture()[0],
            "CPU Model": self.get_cpu_model(),
            "CPU Cores": str(os.cpu_count() or "Unknown"),
            "Total memory": str(memory),
            "Current Working Directory": os.getcwd(),
            "User name": os.getenv("USER") or os.getenv("USERNAME") or "Unknown",
            "UID": str(os.getuid()) if hasattr(os, "getuid") else "N/A",
            "GID": str(os.getgid()) if hasattr(os, "getgid") else "N/A",
            "TERM": os.getenv("TERM", "Unknown"),
            "Default Encoding": sys.getdefaultencoding(),
            "Default Shell": os.getenv("SHELL", "Unknown"),
            "Terminal Emulator": os.getenv("TERM_PROGRAM", "Unknown"),
            "Python Version": platform.python_version(),
            "Python Implementation": platform.python_implementation(),
            "Python Compiler": platform.python_compiler(),
            "Python executable": sys.executable,
            # "Environment Variables": str(os.environ),   #! this should be its own section.
        }

    def get_cpu_model(self) -> str:
        system = platform.system()

        if system == "Linux":
            try:
                with open("/proc/cpuinfo") as f:
                    for line in f:
                        if "model name" in line:
                            return line.split(":", 1)[1].strip()
            except Exception:
                pass

        elif system == "Darwin":
            try:
                stream = os.popen("sysctl -n machdep.cpu.brand_string")
                return stream.read().strip()
            except Exception:
                pass

        elif system == "Windows":
            # This isn't always reliable, but it's better than nothing
            return os.environ.get("PROCESSOR_IDENTIFIER", "Unknown")

        # Fallback
        return platform.processor() or "Unknown" 


class SysInfo(TDEApp):

    APP_NAME = "System Information"
    APP_ID = "sysinfo"
    ICON = "🛈"
    DESCRIPTION = "View static system info such as OS, CPU, UID/GID, etc."

    def get_launch_mode(self) -> LaunchMode:
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
        return SysInfoWidget


    def get_custom_window_settings(self) -> CustomWindowSettings:
        """Returns the settings for the window to be created. \n

        This is not part of the contract and not necessary to implement.
        This method can be optionally implemented to provide custom window settings.
        """
        return {
            # This returns an empty dictionary when not overridden.
            # see CustomWindowSettings for more options
        }