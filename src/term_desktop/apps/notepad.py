"notepad.py"

# python imports
from __future__ import annotations
# from typing import Any #, Type

# Textual imports
from textual import on, events, work
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import TextArea, Button  # , Static
from textual.containers import Horizontal, Container
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.geometry import Offset


# Local imports
from term_desktop.app_sdk.appbase import (TDEApp, LaunchMode, CustomWindowSettings,)


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
        await self.app.push_screen_wait(NotepadMenu(menu_offset=absolute_offset, command_bar=self))

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

        menu.offset = Offset(self.menu_offset.x, self.menu_offset.y + 1)  # +1 to go below the button

    def on_mouse_up(self) -> None:

        self.dismiss(None)

    @on(Button.Pressed)
    async def button_pressed(self, event: Button.Pressed) -> None:

        if event.button.id == "new_note":
            pass


class NotepadWidget(Widget):

    DEFAULT_CSS = """
    TextArea { border: none !important; }
    """

    def compose(self) -> ComposeResult:

        yield CommandBar()
        yield TextArea()

    def on_mount(self) -> None:

        self.query_one(TextArea).focus()

    def on_focus(self) -> None:
        self.query_one(TextArea).focus()

    @on(events.DescendantFocus)
    def descendant_focused(self, event: events.DescendantFocus) -> None:

        self.query_one(CommandBar).add_class("focused")

    @on(events.DescendantBlur)
    def descendant_blurred(self, event: events.DescendantBlur) -> None:

        self.query_one(CommandBar).remove_class("focused")


class Notepad(TDEApp):

    APP_NAME = "Notepad"
    APP_ID = "notepad"
    ICON = "📝"
    DESCRIPTION = "TDE Notepad, simple text editor for TDE."

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
        return NotepadWidget


    def get_custom_window_settings(self) -> CustomWindowSettings:
        """Returns the settings for the window to be created. \n

        This is not part of the contract and not necessary to implement.
        This method can be optionally implemented to provide custom window settings.
        """
        return {
            # This returns an empty dictionary when not overridden.
            # see CustomWindowSettings for more options
        }