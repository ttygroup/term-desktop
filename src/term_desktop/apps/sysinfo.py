"""
sysinfo.py
"""

# Python imports
from __future__ import annotations
from typing import Any, Type
import os
import sys
import platform

# Textual imports
from textual import on
# from textual.content import Content
from textual.widgets import Static
from textual.binding import Binding
import textual.events as events
# from rich.text import Text

# Textual library imports
# Would go here if you have any

# Local imports
from term_desktop.appbase import TermDApp


class SysInfo(TermDApp):

    APP_NAME = "SysInfo"          
    APP_ID = "sysinfo"     

    DEFAULT_CSS = """
    SysInfo {
        width: 45;
        height: 26;
        & > #content_pane { 
            padding: 0 0 0 1;
            overflow-x: auto;            
            & > #title { border: solid $primary; }
            & > #content { width: auto; height: auto; }
        }  
    }    
    """
    BINDINGS = [
        Binding("ctrl+w", "close_window", "Close Window", priority=True),
        Binding("ctrl+d", "minimize_window", "Minimize Window", priority=True),
        # You can remove the above bindings if you dont want them.
        # Note that `close_window` and `minimize_window` are already defined in the base 
        # Textual-Window library, but the base class does not have priority set to True.
        # Priority will make close and minimize shortcuts work even when you have focus
        # on children inside of the window, like TextArea or Input widgets.

        # Add any additional bindings you need here.
    ]

    def __init__(self, id: str, **kwargs: Any):
        super().__init__(       #! Note you cant set id here. It must be set using APP_ID above.
            id=id,              # it must be taken as an argument and passed to super().__init__.
            start_open=True,            # The app sets the window IDs and manages them.
            allow_maximize=True,
            starting_horizontal="centerright",
            starting_vertical="middle",
            # Customize window settings here
            **kwargs
        )
        self.static_system_info = self.get_static_system_info()

    def compose(self):

        yield Static("System Information", id="title")
        yield Static(
            "\n".join(f"{key}: {value}" for key, value in self.static_system_info.items()),
            id="content",
        )

    @on(events.Focus)
    def on_mount(self) -> None:
        # Here you can set which widgets inside the window you would like to gain focus
        # when the window is focused or first opened.
        content = self.query_one("#content", Static)
        content_pane = self.query_one("#content_pane")
        index = content_pane.children.index(content)
        self.log(f"Focused widget: {content} at index {index}")

    def get_static_system_info(self) -> dict[str, str]:
        uname = platform.uname()
        if hasattr(os, 'sysconf'):
            memory = f"{round(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024. ** 3), 2)} GB"
        else:
            memory = "Unknown"


        return {
            "OS": f"{uname.system} {uname.release}",
            "Freedesktop_os label": str(platform.freedesktop_os_release().get('PRETTY_NAME', 'Unknown')),
            "Machine": uname.machine,
            "Architecture": platform.architecture()[0],
            "CPU Model": self.get_cpu_model(),
            "CPU Cores": str(os.cpu_count() or "Unknown"),
            "Total memory": str(memory),
            "Current Working Directory": os.getcwd(),
            "User name": os.getenv("USER") or os.getenv("USERNAME") or "Unknown",
            "UID": str(os.getuid()) if hasattr(os, 'getuid') else "N/A",
            "GID": str(os.getgid()) if hasattr(os, 'getgid') else "N/A",            
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

##############
# ~ Loader ~ #
##############
#? This function is used by the app loader to load the app.
# It must return the class definition of the app, not an instance.
# (That is what Type[TermDApp] means in the return type hint.)

# Note that it's very important to the architecture of the app that this
# loader returns a class definition and not an instance.
# We don't want every app to be booted up along with the desktop environment!
# Term-Desktop only initializes the class on demand when it needs to.

def loader() -> Type[TermDApp]:
    return SysInfo     #! Replace SysInfo with your app class name.