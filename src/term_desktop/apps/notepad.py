"notepad.py"

# python imports
from __future__ import annotations
from typing import Any, Type

# Textual imports
from textual import on, events, work
from textual.app import ComposeResult
from textual.widgets import TextArea, Button  # , Static
from textual.containers import Horizontal, Container
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.geometry import Offset

# Textual library imports
# from textual_window.window import TopBar

# Local imports
from term_desktop.appbase import TermDApp
# from term_desktop.common import SimpleButton

# from term_desktop.datawidgets import CurrentPath



class CommandBar(Horizontal):

    DEFAULT_CSS = """
    CommandBar { 
        height: 1;
        padding: 0;
        background: $panel-lighten-1;
        border-left: wide $panel-lighten-1;
        border-right: wide $panel-lighten-1;
        & > Button {
            background: transparent;
            min-width: 6;
            &:hover { background: $primary-darken-2; }
            &:focus {
                background: $primary-darken-2;
                text-style: none;
            }                    
        }
        &.focused {
            background: $secondary;
            border-left: wide $secondary;
            border-right: wide $secondary;
        }
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the command bar with a static text area."""
        yield Button("File", id="file_button")
        yield Button("Edit", id="edit_button")
        yield Button("View", id="view_button")
        yield Button("Help", id="help_button")

    def on_mount(self) -> None:

        buttons = self.query_children(Button).results()
        for button in buttons:
            button.compact = True

    @work
    async def show_popup(self, button: Button) -> None:

        absolute_offset = self.screen.get_offset(button)
        await self.app.push_screen_wait(
            NotepadMenu(
                menu_offset=absolute_offset,
                command_bar=self
            )
        )

    @on(Button.Pressed)
    async def file_button_pressed(self, event: Button.Pressed) -> None:
        self.show_popup(event.button)


class NotepadMenu(ModalScreen[None]):


    BINDINGS = [
        Binding("escape", "dismiss", "Dismiss Menu"),
    ]

    CSS = """
    NotepadMenu {
        background: $background 0%;
        align: left top;         /* This will set the starting coordinates to (0, 0) Which we need... */
        & > #menu_container {                       /* ...because of the absolute offsets */
            background: $surface;
            width: 14; height: 6;
            border-left: wide $panel;
            border-right: wide $panel;        
            &.bottom { border-top: hkey $panel; }
            &.top { border-bottom: hkey $panel; }
            & > Button {
                min-width: 6;
                &:focus { text-style: none; background: $primary-darken-2; }
                &:hover { background: $panel-lighten-2; }
                &.pressed { background: $primary; }        
            }
        }
    }  

    """

    def __init__(
        self,
        menu_offset: Offset,
        command_bar: CommandBar,
    ) -> None:

        super().__init__()
        self.menu_offset = menu_offset
        self.command_bar = command_bar

    def compose(self) -> ComposeResult:

        with Container(id="menu_container"):

            yield Button("New", id="new_note")
            yield Button("New Window", id="new_window")
            yield Button("Open", id="open_file")
            yield Button("Save", id="save_file")
            yield Button("Save As", id="save_file_as")
            yield Button("Exit", id="exit")

    def on_mount(self) -> None:

        menu = self.query_one("#menu_container")
        buttons = menu.query_children(Button).results()
        for button in buttons:
            button.compact = True

        menu.offset = Offset(self.menu_offset.x, self.menu_offset.y + 1) # +1 to go below the button

    def on_mouse_up(self) -> None:

        self.dismiss(None)

    @on(Button.Pressed)
    async def button_pressed(self, event: Button.Pressed) -> None:

        if event.button.id == "new_note":
            pass



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
            icon="📝",
            start_open=True, 
            allow_maximize=True, 
            **kwargs
        )

    def compose(self) -> ComposeResult:

        yield TextArea()

    def on_mount(self) -> None:

        self.mount(CommandBar(), after="TopBar")
        self.query_one(TextArea).focus()

    def on_focus(self) -> None:
        self.query_one(TextArea).focus()

    @on(events.DescendantFocus)
    def descendant_focused(self, event: events.DescendantFocus) -> None:

        self.query_one(CommandBar).add_class("focused")

    @on(events.DescendantBlur)
    def descendant_blurred(self, event: events.DescendantBlur) -> None:

        self.query_one(CommandBar).remove_class("focused")


def loader() -> Type[TermDApp]:
    return Notepad
