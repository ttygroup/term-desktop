"term-desktop"

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING  # , cast

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.widgets.directory_tree import DirEntry

# Textual imports
from textual import on, events  # , work
from textual.widgets import (
    DirectoryTree,
)
from textual.binding import Binding
from textual.screen import Screen

# Textual library imports
from textual_window import Window, WindowSwitcher
from textual_slidecontainer import SlideContainer

#################
# Local imports #
#################
# from term_desktop.app_sdk.appbase import TDEApp
from term_desktop.services import ServicesWidget
from term_desktop.common import (
    DummyScreen,
)
from term_desktop.core import (
    StartMenu,
    TaskBar,
    Desktop,
    FileExplorer,
    ExplorerPathBar,
    AppChooser,
)
from term_desktop.common.messages import (
    ToggleStartMenu,
    ToggleExplorer,
    ToggleTaskBar,
    ToggleWindowSwitcher,
)


class MainScreen(Screen[None]):

    BINDINGS = [
        Binding("f1", "toggle_startmenu", "Quick Launcher"),
        Binding("f2", "toggle_explorer", "File Explorer"),
        Binding("f3", "toggle_windowbar", "Window Bar"),
        Binding("f4", "toggle_windowswitcher", "Window Switcher"),
        Binding("f12", "toggle_transparency", "Toggle Transparency"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.styles.opacity = 0

    def compose(self) -> ComposeResult:

        ##############################
        ### SCREEN PUSHING WIDGETS ###
        yield WindowSwitcher(cycle_key="f4")

        ######################
        ### DOCKED WIDGETS ###
        yield FileExplorer()  # the order these are in is important for the layout
        yield ExplorerPathBar()
        yield StartMenu()
        yield TaskBar(start_open=True)

        ###############
        ### DESKTOP ###
        yield Desktop(id="main_desktop")

        # NOTE: Windows are mounted into the Desktop container.

    def on_mount(self) -> None:
        services = self.app.query_one(ServicesWidget).services
        services.window_service.register_mounting_callback(
            self.mounting_callback,
            callback_id="main_desktop",
        )
        self.set_timer(0.3, self.finish_mounting)

    def finish_mounting(self) -> None:
        self.styles.animate("opacity", 1.0, duration=0.5)

    async def mounting_callback(self, window: Window) -> None:
        await self.query_one(Desktop).mount(window)

    ###############
    # ~ Actions ~ #
    ###############

    def action_toggle_transparency(self) -> None:
        self.app.ansi_color = not self.app.ansi_color
        self.app.push_screen(DummyScreen())

    @on(ToggleTaskBar)
    def action_toggle_windowbar(self) -> None:
        """Toggle the visibility of the window bar."""
        self.query_one(TaskBar).toggle_bar()

    @on(ToggleWindowSwitcher)
    def action_toggle_windowswitcher(self) -> None:
        """Toggle the visibility of the window switcher."""
        self.query_one(WindowSwitcher).show()

    @on(ToggleExplorer)
    def action_toggle_explorer(self) -> None:
        """Toggle the visibility of Slide Menu 1."""
        explorer = self.query_one(FileExplorer)
        path_bar = self.query_one(ExplorerPathBar)
        explorer.toggle()
        path_bar.toggle()

    @on(ToggleStartMenu)
    def action_toggle_startmenu(self) -> None:
        """Open the start menu / quick launcher."""
        self.query_one(StartMenu).toggle()

    ####################
    # ~ Other Events ~ #
    ####################

    @on(events.Click)
    async def handle_click(self, event: events.Click):
        """This method exists to make the start menu close if someone clicks
        elsewhere on the screen while it is open"""

        start_menu = self.query_one(StartMenu)
        if not start_menu.state:  # if its currently closed, do nothing.
            return
        if event.widget:
            if (
                event.widget is not self.query_one(StartMenu)  # not the start menu
                and event.widget not in start_menu.query().results()  # not inside the start menu
                and event.widget is not self.query_one(TaskBar).query_one("#start_button")
            ):
                await self.run_action("toggle_startmenu")

    @on(TaskBar.DockToggled)
    def taskbar_dock_toggled(self, event: TaskBar.DockToggled) -> None:

        self.query_one(FileExplorer).shift_ui_for_taskbar(event.dock)
        self.query_one(ExplorerPathBar).shift_ui_for_taskbar(event.dock)
        self.query_one(StartMenu).shift_ui_for_taskbar(event.dock)

    @on(SlideContainer.SlideCompleted, "FileExplorer")
    def slide_completed_explorer(self, event: SlideContainer.SlideCompleted) -> None:

        if not event.state:
            taskbar = self.query_one(TaskBar)
            taskbar.refresh_buttons()  # this is to fix a graphical glitch.

    @on(DirectoryTree.FileSelected)
    def file_selected(self, event: DirectoryTree.FileSelected) -> None:

        if event.node.data:
            path = event.node.data.path
            self.app.push_screen(AppChooser(path))

    @on(DirectoryTree.NodeHighlighted)
    def node_highlighted(self, event: DirectoryTree.NodeHighlighted[DirEntry]) -> None:

        if event.node.data:
            path_bar = self.query_one(ExplorerPathBar)
            path_bar.update_path(event.node.data.path)
        else:
            self.log.error("Node data is None, cannot update path.")
