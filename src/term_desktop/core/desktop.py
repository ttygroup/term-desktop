"desktop.py"

# python standard library imports
from __future__ import annotations

# Textual imports
from textual import on, events  # , work
from textual.app import ComposeResult
from textual.containers import Container

# Textual library imports
from textual_pyfiglet import FigletWidget
from textual_hires_canvas import Canvas  # , HiResMode

# from textual_coloromatic import Coloromatic


__all__ = [
    "Desktop",
]


class CustomCanvas(Canvas):

    def __init__(self) -> None:
        super().__init__()
        self.styles.width = "1fr"
        self.styles.height = "1fr"
        self.styles.layer = "canvas"

    @on(Canvas.Resize)
    def handle_canvas_resize(self, event: Canvas.Resize) -> None:
        self.reset(size=event.size, refresh=True)

    def clear_canvas(self) -> None:
        """Clear the canvas."""

        assert self._canvas_size, "Invalid canvas size."
        width = self._canvas_size.width
        height = self._canvas_size.height
        self._buffer = [[" "] * width for _ in range(height)]
        self._styles = [[""] * width for _ in range(height)]
        self.refresh()

    def on_mouse_down(self, event: events.MouseDown) -> None:

        if event.button == 1:  # left button
            self.position_on_down = event.offset
            self.capture_mouse()

    def on_mouse_up(self) -> None:
        self.release_mouse()
        self.clear_canvas()

    def on_mouse_move(self, event: events.MouseMove) -> None:

        if self.app.mouse_captured == self:
            self.clear_canvas()

            # Get the absolute position of the mouse right now (event.screen_offset),
            # minus where it was when the mouse was pressed down (position_on_down).
            total_delta = event.offset - self.position_on_down

            self.draw_rectangle_box(
                x0=self.position_on_down.x,
                y0=self.position_on_down.y,
                x1=self.position_on_down.x + total_delta.x,
                y1=self.position_on_down.y + total_delta.y,
                style="bold cyan",
            )


class Desktop(Container):

    def __init__(self, id: str) -> None:
        super().__init__(id=id)

    def compose(self) -> ComposeResult:

        # yield Coloromatic(pattern="brick2")
        with CustomCanvas(): 
            yield FigletWidget(
                "T",
                font="dos_rebel",
                colors=["$primary", "$primary", "$accent", "$primary"],
                animate=True,
                horizontal=True,
                gradient_quality=30,
            )
            yield FigletWidget(
                "D",
                font="dos_rebel",
                colors=["$primary", "$accent", "$primary", "$primary"],
                animate=True,
                horizontal=True,
                gradient_quality=30,
            )
            yield FigletWidget(
                "E",
                font="dos_rebel",
                colors=["$primary", "$primary", "$primary", "$accent"],
                animate=True,
                horizontal=True,
                gradient_quality=30,
            )
