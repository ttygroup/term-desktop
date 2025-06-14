"""template.py

# To customize this template:
# 1. Change APP_NAME and APP_ID
# 2. Replace Template class name throughout
# 3. Update the loader() function return value
# 4. Build your widget using compose() as normal.
"""

# Python imports
from __future__ import annotations
from typing import Any, Type

# Textual imports
from textual import on
from textual.widgets import Static
from textual.binding import Binding
import textual.events as events

# Textual library imports
# Would go here if you have any

# Local imports
from term_desktop.appbase import TermDApp


class Template(TermDApp):

    # APP_NAME = "Template"   # For display purposes, it can have spaces and special characters.
    # APP_ID = "template"     # For internals. The same as `id` in any widget.

    APP_NAME = None  # The validation will fail if either of these are not set.
    APP_ID = None

    DEFAULT_CSS = """
    Template {
        width: 45;
        height: 25;
        & > #content_pane { 
            /* padding: 1 0;  You'd change CSS for #content_pane here */
            & > #my_static { border: solid red; }
                /* Any widgets inside the window have to have CSS set inside of #content_pane */
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
        super().__init__(  #! Note you cant set id here. It must be set using APP_ID above.
            id=id,  # it must be taken as an argument and passed to super().__init__.
            start_open=True,  # The app sets the window IDs and manages them.
            allow_maximize=True,
            starting_horizontal="centerright",
            starting_vertical="middle",
            # Customize window settings here
            **kwargs,
        )

    def compose(self):

        yield Static("Your app content goes here", id="my_static")

    @on(events.Focus)
    def on_mount(self) -> None:
        # Here you can set which widgets inside the window you would like to gain focus
        # when the window is focused or first opened.
        self.query_one("#my_static", Static).focus()

    # The mount and focus methods can be split into two methods if you need to:
    # def on_focus(self) -> None:
    #     self.query_one("#my_static", Static).focus()


##############
# ~ Loader ~ #
##############
# ? This function is used by the app loader to load the app.
# It must return the class definition of the app, not an instance.
# (That is what Type[TermDApp] means in the return type hint.)

# Note that it's very important to the architecture of the app that this
# loader returns a class definition and not an instance.
# We don't want every app to be booted up along with the desktop environment!
# Term-Desktop only initializes the class on demand when it needs to.


def loader() -> Type[TermDApp]:
    return Template  #! Replace Template with your app class name.
