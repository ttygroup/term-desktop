"notepad.py"

# python imports
from __future__ import annotations
from typing import Any, Type

# Textual imports
# from textual import on
from textual.app import ComposeResult
# import textual.events as events
from textual.widgets import TextArea #, Static
from textual.containers import Horizontal
from textual.binding import Binding

# Textual library imports


# Local imports
from term_desktop.appbase import TermDApp
from term_desktop.common import SimpleButton

# from term_desktop.datawidgets import CurrentPath

class CommandBar(Horizontal):

    def compose(self) -> ComposeResult:
        """Compose the command bar with a static text area."""
        yield SimpleButton("File", classes="command_bar_button")
        yield SimpleButton("Edit", classes="command_bar_button")
        yield SimpleButton("View", classes="command_bar_button")
        yield SimpleButton("Help", classes="command_bar_button")


class Notepad(TermDApp):

    APP_NAME = "Notepad"
    APP_ID = "notepad"

    DEFAULT_CSS = """
    Notepad {
        width: 45; height: 25;
        margin: 0;
        & > #content_pane { 
            padding: 0 0 1 0;
            & > TextArea { border: none !important; }
            & > CommandBar { 
                height: 1;
                background: $panel;
                padding: 0;
                & > .command_bar_button { width: 6; }
            }
        }  
    }    
    """
    BINDINGS = [
        Binding("ctrl+s", "save", "Save Notepad", priority=True),
        Binding("ctrl+f", "find", "Find in Notepad"),
        Binding("ctrl+w", "close_window", "Close Window", priority=True),
        Binding("ctrl+d", "minimize_window", "Minimize Window", priority=True),        
    ]

    def __init__(self, **kwargs: Any):
        super().__init__(
            start_open=True,
            allow_maximize=True,
            **kwargs
        )

    def compose(self) -> ComposeResult:

        yield CommandBar()
        yield TextArea()  

    def on_mount(self) -> None:
        self.query_one(TextArea).focus()

    def on_focus(self) -> None:
        self.query_one(TextArea).focus()



def loader() -> Type[TermDApp]:
    return Notepad