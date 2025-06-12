"taskbar.py - A task bar for the SSH Desktop application."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from textual.visual import VisualType
    import textual.events as events

# Textual imports
# from textual import on
# from textual.widgets import Static
# from textual.css.query import NoMatches

# Textual library imports
from textual_window import WindowBar

# Local imports
from term_desktop.common import NoSelectStatic
# from term_desktop.core import StartMenuContainer as StartMenu
from term_desktop.messages import ToggleStartMenu, ToggleExplorer


class TaskBarButton(NoSelectStatic):

    def __init__(self, content: VisualType, window_bar: WindowBar, **kwargs: Any):
        super().__init__(content=content, **kwargs)
        self.window_bar = window_bar
        self.click_started_on: bool = False

        if not hasattr(self, "on_mouse_up"):
            raise NotImplementedError(
                f"{self.__class__.__name__} must implement the on_mouse_up method."
            )

    def on_mouse_down(self, event: events.MouseDown) -> None:

        if event.button == 1:  # left click
            self.add_class("pressed")
        elif event.button == 2 or event.button == 3:  # middle or right click
            self.add_class("right_pressed")
        self.click_started_on = True


    def on_leave(self, event: events.Leave) -> None:

        self.remove_class("pressed")
        self.remove_class("right_pressed")
        self.click_started_on = False 



class StartButton(TaskBarButton):

    async def on_mouse_up(self, event: events.MouseUp) -> None:

        self.remove_class("pressed")
        self.remove_class("right_pressed")
        if self.click_started_on:
            if event.button == 1:  # left click
                self.post_message(ToggleStartMenu())
            elif event.button == 2 or event.button == 3:  # middle or right click
                # self.show_popup()
                pass
            self.click_started_on = False


class ExplorerButton(TaskBarButton):

    async def on_mouse_up(self, event: events.MouseUp) -> None:

        self.remove_class("pressed")
        self.remove_class("right_pressed")
        if self.click_started_on:
            if event.button == 1:  # left click
                self.post_message(ToggleExplorer())
            elif event.button == 2 or event.button == 3:  # middle or right click
                # self.show_popup()
                pass
            self.click_started_on = False


class TaskBar(WindowBar):

    async def on_mount(self):
        await self.mount(
            StartButton(
                content="🚀",
                window_bar=self,
                id="start_button",
            ),
            before=self.query_one("#windowbar_button_left"),
        )   
        await self.mount(
            ExplorerButton(
                content="📁",
                window_bar=self,
                id="explorer_button",
            ),
            before=self.query_one("#windowbar_button_left"),
        )           
