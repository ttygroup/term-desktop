"appchooser.py"

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual import events
from pathlib import Path

# Textual imports
from textual.containers import Vertical, Right
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.widgets import (
    Static,
    OptionList,
    Checkbox,
    Button,
)

# Local imports
from term_desktop.appbase import TermDApp


class AppChooser(ModalScreen[TermDApp]):
    """A modal screen for choosing an application to run a selected file."""

    BINDINGS = [
        Binding("enter", "ok", "Ok"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, file_path: Path) -> None:
        super().__init__(id="app_chooser")
        self.file_path = file_path

    def compose(self) -> ComposeResult:

        with Vertical():
            yield Static("How do you want to open this file?")
            yield OptionList()
            with Right():
                yield Checkbox("Always use this app")
            with Right():
                yield Button("Ok", id="ok_button")

    def on_click(self, event: events.Click):

        children = self.query().results()
        if event.widget:
            from_self = event.widget in children
            if not from_self:
                self.dismiss()
        else:
            self.log.error(f"No Widget: {event.widget = }")

    def action_cancel(self) -> None:
        """Handle the cancel action."""
        self.dismiss()

    def action_ok(self) -> None:
        """Handle the ok action."""
        self.dismiss()
