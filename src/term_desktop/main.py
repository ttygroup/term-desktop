"term-desktop"

# python standard library imports
from __future__ import annotations

# from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # from textual.widgets.directory_tree import DirEntry
    from textual.visual import VisualType
    from textual.app import ComposeResult
    import textual.events as events  
    # from textual.css.query import QueryType


# Textual imports
from textual import on  # , work
from textual.app import App
from textual.widgets import (
    Header,
    DirectoryTree,
    OptionList,
    # Static,
    # Button,
)
from textual.containers import (
    Container,
    # Horizontal,
    # Vertical,
)
from textual.binding import Binding
from textual.signal import Signal

# from textual.widget import Widget
# from rich.text import Text
# import rich.repr
# from textual.screen import Screen

# Textual library imports
from textual_pyfiglet import FigletWidget
from textual_window import WindowBar, WindowSwitcher #, Window
from textual_slidecontainer import SlideContainer

# Local imports
from term_desktop.common import NoSelectStatic, CurrentPath
from term_desktop.datawidgets import DataWidgetsContainer
from term_desktop.core import StartMenu, FileExplorer
from term_desktop.messages import (ToggleStartMenu, ToggleWindowSwitcher, ToggleWindowBar,)
from term_desktop.apps import (
    Notepad,
    # TaskfileWindow,
)

class StartButton(NoSelectStatic):

    def __init__(self, content: VisualType, window_bar: WindowBar, **kwargs: Any):
        super().__init__(content=content, **kwargs)
        self.window_bar = window_bar
        self.click_started_on: bool = False

    def on_mouse_down(self, event: events.MouseDown) -> None:

        if event.button == 1:  # left click
            self.add_class("pressed")
        elif event.button == 2 or event.button == 3:  # middle or right click
            self.add_class("right_pressed")
        self.click_started_on = True

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

    def on_leave(self, event: events.Leave) -> None:

        self.remove_class("pressed")
        self.remove_class("right_pressed")
        self.click_started_on = False

    # @work
    # async def show_popup(self) -> None:

    #     absolute_offset = self.screen.get_offset(self)
    #     await self.app.push_screen_wait(
    #         WindowBarMenu(
    #             menu_offset=absolute_offset,
    #             dock=self.window_bar.dock,
    #             window=self.window,
    #         )
    #     )


class TermDesktop(App[None]):

    TITLE = "Term-Desktop"
    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("f4", "toggle_startmenu", "Quick Launcher"),
        Binding("ctrl+e", "toggle_windowbar", "Window Bar"),
        Binding("f1", "toggle_windowswitcher", "Window Switcher"),
        Binding("f2", "toggle_explorer", "File Explorer"),
    ]

    def __init__(self):
        super().__init__()
        self.path_changed_signal: Signal[Path] = Signal(self, "path-changed")

    def compose(self) -> ComposeResult:

        #########################
        ### INVISIBLE WIDGETS ###
        
        with DataWidgetsContainer():
            yield CurrentPath()
        yield WindowSwitcher()

        #########################
        
        yield FileExplorer()  
        yield StartMenu()        
        yield WindowBar(start_open=True)    # windowbar must go before header
        yield Header(show_clock=True)      

        with Container(id="main_desktop"):

            yield FigletWidget(
                "Term - Desktop",
                font="dos_rebel",
                colors=["$primary", "$primary", "$primary", "$accent"],
                animate=True,
                horizontal=True,
                id="background_figlet",
            )

    async def on_mount(self) -> None:

        windowbar = self.query_one(WindowBar)

        await windowbar.mount(
            StartButton(
                content="🚀",
                window_bar=windowbar,
                id="start_button",
            ),
            before=self.query_one("#windowbar_button_left"),
        )

    #########################
    # ~ Actions and Events~ #
    #########################

    @on(ToggleWindowBar)
    def action_toggle_windowbar(self) -> None:
        """Toggle the visibility of the window bar."""
        self.query_one(WindowBar).toggle_bar()

    @on(ToggleWindowSwitcher)
    def action_toggle_windowswitcher(self) -> None:
        """Toggle the visibility of the window switcher."""
        self.query_one(WindowSwitcher).show()

    @on(ToggleStartMenu)
    def action_toggle_startmenu(self) -> None:
        """Toggle the visibility of the start menu."""
        slide_menu = self.query_one("#start_menu", SlideContainer)
        slide_menu.toggle()

    @on(SlideContainer.SlideCompleted, "#start_menu")
    def slide_completed_startmenu(self, event: SlideContainer.SlideCompleted) -> None:
        """Handle the slide completion event."""
        if event.state:
            event.container.query_one(OptionList).focus()
        else:
            event.container.query_children().blur()

    @on(SlideContainer.SlideCompleted, "#file_explorer")
    def slide_completed_explorer(self, event: SlideContainer.SlideCompleted) -> None:
        """Handle the slide completion event."""
        if event.state:
            event.container.query_one(DirectoryTree).focus()
        else:
            event.container.query_children().blur()

    @on(DirectoryTree.FileSelected)
    def file_selected(self, event: DirectoryTree.FileSelected) -> None:

        current_path = self.query_one(CurrentPath).path
        main_desktop = self.query_one("#main_desktop")
        main_desktop.mount(Notepad(current_path=current_path))

    # @on(DirectoryTree.DirectorySelected)
    # def node_selected(self, event: DirectoryTree.NodeExpanded[DirEntry]) -> None:

    #     if event.node.data:
    #         path = event.node.data.path
    #         self.log(path)
    #         self.query_one(CurrentPath).path = path
    #         # self.query_one(TaskfileWindow).update_path()

    def action_toggle_explorer(self) -> None:
        """Toggle the visibility of Slide Menu 1."""
        explorer = self.query_one(FileExplorer)
        explorer.toggle()            


####################
# ~ Run function ~ #
####################


def run():
    TermDesktop().run()
