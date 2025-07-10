"""
calculator.py

The calculator app from the examples folder in the Textual github repository.
"""

# Python imports
from __future__ import annotations

# from typing import Any, Type
from decimal import Decimal

# Textual imports
from textual import on, events
from textual.app import ComposeResult
from textual.containers import Container
from textual.css.query import NoMatches
from textual.reactive import var
from textual.widgets import Button, Digits

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


class CalculatorMeta(TDEAppBase):

    APP_NAME = "Calculator"
    APP_ID = "calculator"
    ICON = "🧮"
    DESCRIPTION = "Calculate things, mostly numbers."
    APP_AUTHOR = "Lifted from Textual examples by the TDE team"

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
        return CalculatorApp

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
            "width": 33,  #
            "height": 30,  #
            # "max_width": None,  #  default is 'size of the parent container'
            # "max_height": None,  # default is 'size of the parent container'
            "min_width": 33,  #
            "min_height": 30,  #
        }


class CalculatorApp(TDEMainWidget):
    """A working 'desktop' calculator."""

    DEFAULT_CSS = """
    #calculator {
        layout: grid;
        grid-size: 4;
        grid-gutter: 1 2;
        grid-columns: 1fr;
        grid-rows: 2fr 1fr 1fr 1fr 1fr 1fr;
        margin: 1 2;
        min-height: 25;
        min-width: 26;
        height: 100%;
        &:inline {
            margin: 0 2;
        }
    }
    Button {
        width: 100%;
        height: 100%;
    }
    #numbers {
        column-span: 4;
        padding: 0 1;
        height: 100%;
        background: $panel;
        color: $text;
        content-align: center middle;
        text-align: right;
    }
    #number-0 { column-span: 2; }
    """

    numbers = var("0")
    show_ac = var(True)
    left = var(Decimal("0"))
    right = var(Decimal("0"))
    value = var("")
    operator = var("plus")

    # Maps button IDs on to the corresponding key name
    NAME_MAP = {
        "asterisk": "multiply",
        "slash": "divide",
        "underscore": "plus-minus",
        "full_stop": "point",
        "plus_minus_sign": "plus-minus",
        "percent_sign": "percent",
        "equals_sign": "equals",
        "minus": "minus",
        "plus": "plus",
    }

    def watch_numbers(self, value: str) -> None:
        """Called when numbers is updated."""
        self.query_one("#numbers", Digits).update(value)

    def compute_show_ac(self) -> bool:
        """Compute switch to show AC or C button"""
        return self.value in ("", "0") and self.numbers == "0"

    def watch_show_ac(self, show_ac: bool) -> None:
        """Called when show_ac changes."""
        self.query_one("#c").display = not show_ac
        self.query_one("#ac").display = show_ac

    def compose(self) -> ComposeResult:
        """Add our buttons."""
        with Container(id="calculator"):
            yield Digits(id="numbers")
            yield Button("AC", id="ac", variant="primary")
            yield Button("C", id="c", variant="primary")
            yield Button("+/-", id="plus-minus", variant="primary")
            yield Button("%", id="percent", variant="primary")
            yield Button("÷", id="divide", variant="warning")
            yield Button("7", id="number-7", classes="number")
            yield Button("8", id="number-8", classes="number")
            yield Button("9", id="number-9", classes="number")
            yield Button("x", id="multiply", variant="warning")
            yield Button("4", id="number-4", classes="number")
            yield Button("5", id="number-5", classes="number")
            yield Button("6", id="number-6", classes="number")
            yield Button("-", id="minus", variant="warning")
            yield Button("1", id="number-1", classes="number")
            yield Button("2", id="number-2", classes="number")
            yield Button("3", id="number-3", classes="number")
            yield Button("+", id="plus", variant="warning")
            yield Button("0", id="number-0", classes="number")
            yield Button(".", id="point")
            yield Button("=", id="equals", variant="warning")

    def on_key(self, event: events.Key) -> None:
        """Called when the user presses a key."""

        def press(button_id: str) -> None:
            """Press a button, should it exist."""
            try:
                self.query_one(f"#{button_id}", Button).press()
            except NoMatches:
                pass

        key = event.key
        if key.isdecimal():
            press(f"number-{key}")
        elif key == "c":
            press("c")
            press("ac")
        else:
            button_id = self.NAME_MAP.get(key)
            if button_id is not None:
                press(self.NAME_MAP.get(key, key))

    @on(Button.Pressed, ".number")
    def number_pressed(self, event: Button.Pressed) -> None:
        """Pressed a number."""
        assert event.button.id is not None
        number = event.button.id.partition("-")[-1]
        self.numbers = self.value = self.value.lstrip("0") + number

    @on(Button.Pressed, "#plus-minus")
    def plus_minus_pressed(self) -> None:
        """Pressed + / -"""
        self.numbers = self.value = str(Decimal(self.value or "0") * -1)

    @on(Button.Pressed, "#percent")
    def percent_pressed(self) -> None:
        """Pressed %"""
        self.numbers = self.value = str(Decimal(self.value or "0") / Decimal(100))

    @on(Button.Pressed, "#point")
    def pressed_point(self) -> None:
        """Pressed ."""
        if "." not in self.value:
            self.numbers = self.value = (self.value or "0") + "."

    @on(Button.Pressed, "#ac")
    def pressed_ac(self) -> None:
        """Pressed AC"""
        self.value = ""
        self.left = self.right = Decimal(0)
        self.operator = "plus"
        self.numbers = "0"

    @on(Button.Pressed, "#c")
    def pressed_c(self) -> None:
        """Pressed C"""
        self.value = ""
        self.numbers = "0"

    def _do_math(self) -> None:
        """Does the math: LEFT OPERATOR RIGHT"""
        try:
            if self.operator == "plus":
                self.left += self.right
            elif self.operator == "minus":
                self.left -= self.right
            elif self.operator == "divide":
                self.left /= self.right
            elif self.operator == "multiply":
                self.left *= self.right
            self.numbers = str(self.left)
            self.value = ""
        except Exception:
            self.numbers = "Error"

    @on(Button.Pressed, "#plus,#minus,#divide,#multiply")
    def pressed_op(self, event: Button.Pressed) -> None:
        """Pressed one of the arithmetic operations."""
        self.right = Decimal(self.value or "0")
        self._do_math()
        assert event.button.id is not None
        self.operator = event.button.id

    @on(Button.Pressed, "#equals")
    def pressed_equals(self) -> None:
        """Pressed ="""
        if self.value:
            self.right = Decimal(self.value)
        self._do_math()
