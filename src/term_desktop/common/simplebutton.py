# Python imports
from __future__ import annotations
# from typing import TYPE_CHECKING, Any
# if TYPE_CHECKING:
    # from textual.events import Click
    # from textual.app import RenderResult

# from textual.errors import RenderError
from textual.visual import VisualType

# Textual imports
from textual import on, events
from textual.widgets import Static
# from textual.reactive import reactive
from textual.message import Message
from textual.binding import Binding
# from textual.content import Content
# from rich.console import RenderableType
# from rich.text import Text #, TextType


class SimpleButton(Static):
    """A simple button widget. This does not inherit from Button, but from Static.

    This is designed to copy the basic functionality of the Textual button but can be
    as small as 1x1.
    """

    DEFAULT_CSS = """
    SimpleButton {
        width: auto; height: auto;
        text-align: center;
        &:hover { background: $primary-darken-1; }
    }
    """

    BINDINGS = [Binding("enter", "press", "Press button", show=False)]

    class Pressed(Message):
        """Event sent when a `SimpleButton` is pressed.   

        Can be handled using `on_simple_button_pressed` (in a subclass of
        [`Button`][textual.widgets.Button] or in a parent widget in the DOM.)   
        OR   
        by using @on(SimpleButton.Pressed)"""

        def __init__(self, button: SimpleButton) -> None:
            super().__init__()

            self.button: SimpleButton = button
            """The button that was pressed.   
            Note that it is a SimpleButton object.   
            You can access the button's properties:
            - button.id
            - button.name
            - button.index   (if you set an index)
            - etc"""

        @property
        def control(self) -> SimpleButton:
            """This is required to be able to use the 'selector' property
            when using the message handler."""

            return self.button
        
    class HoverEnter(Message):
        def __init__(self, button: SimpleButton) -> None:
            self.button: SimpleButton = button
            """The button that was entered (hovered over)."""
            super().__init__()

        @property
        def control(self) -> SimpleButton:
            return self.button

    class HoverLeave(Message):
        def __init__(self, button: SimpleButton) -> None:
            self.button: SimpleButton = button
            """The button that was left."""
            super().__init__()

        @property
        def control(self) -> SimpleButton:
            return self.button


    def __init__(
            self,
            content: VisualType = "",
            *,
            index: int | None = None,
            expand: bool = False,
            shrink: bool = False,
            markup: bool = True,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
            disabled: bool = False
        ) -> None:
        """
        It can be any size (down to 1x1). It copies the `Pressed` event from normal buttons.

        It contains the `HoverEnter` and `HoverLeave` events, which are triggered when the
        mouse enters or leaves the button. These provide an easy way for hovering over
        a SimpleButton to trigger some action like updating a label or UI elements elsewhere.      

        Args:
            content: A Rich renderable, or string containing console markup.
            index: Allows setting index for the button. This is useful if the button
                is part of a list of buttons. Defaults to None.
            expand: Expand content if required to fill container.
            shrink: Shrink content if required to fill container.
            markup: True if markup should be parsed and rendered.
            name: Name of widget.
            id: ID of Widget.
            classes: Space separated list of class names.
            disabled: Whether the static is disabled or not.    
        """
        super().__init__(
            content = content,
            expand = expand,
            shrink = shrink,
            markup = markup,
            name = name,
            id = id,
            classes = classes,
            disabled = disabled,
        )
        self.can_focus = True
        self.index: int | None = index
    
    def watch_mouse_hover(self, value: bool) -> None:
        """OVERRIDE: Update from CSS if mouse over state changes.
        Textual addition: posts HoverEnter / HoverLeave messages."""

        if self._has_hover_style:
            self._update_styles()
        if value:
            self.post_message(self.HoverEnter(self))
        else:
            self.post_message(self.HoverLeave(self))
    
    @on(events.Click)
    def action_press(self) -> None:
        self.post_message(self.Pressed(self))


    # def on_click(self, event: Click) -> None:
    #     """Called when the button is clicked. Posts a message 'Pressed'.
    #     Use the message handler to handle the event:   
    #     ```
    #     @on(SimpleButton.Pressed)   
    #     def on_button_pressed(self, message: SimpleButton.Pressed) -> None:   
    #         print("Button was pressed!")
    #     ``` """
    #     self.post_message(self.Pressed(self))
