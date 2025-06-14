"term-desktop"

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING, cast  # , Type #, Any
from pathlib import Path

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.widgets.directory_tree import DirEntry

    # import textual.events as events
    # from textual.visual import VisualType
    # from textual.widgets.directory_tree import DirEntry
    # from textual.css.query import QueryType

# from dataclasses import dataclass

# Textual imports
from textual import on, events  # , work
from textual.app import App
from textual.widgets import (
    DirectoryTree,
    # OptionList,
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
from textual.screen import Screen
import rich.repr
from rich.rule import Rule

# from textual.widget import Widget
# from rich.text import Text
# import rich.repr
# from textual.screen import Screen

# Textual library imports
from textual_pyfiglet import FigletWidget
from textual_window import WindowSwitcher

from textual_slidecontainer import SlideContainer

#################
# Local imports #
#################
from term_desktop.appbase import TermDApp
from term_desktop.common import (
    CurrentPath,
    RegisteredApps,
    AppInstanceCounter,
)
from term_desktop.core import (
    StartMenu,
    TaskBar,
    FileExplorer,
    ExplorerPathBar,
    AppChooser,
    AppLoader,
)
from term_desktop.messages import (
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
    ]

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
        with Container(id="main_desktop"):
            yield FigletWidget(
                "Term - Desktop",
                font="dos_rebel",
                colors=["$primary", "$primary", "$primary", "$accent"],
                animate=True,
                horizontal=True,
                id="background_figlet",
            )

    #########################
    # ~ Actions and Events~ #
    #########################

    @on(ToggleTaskBar)
    def action_toggle_windowbar(self) -> None:
        """Toggle the visibility of the window bar."""
        self.query_one(TaskBar).toggle_bar()

    @on(TaskBar.DockToggled)
    def windowbar_dock_toggled(self, event: TaskBar.DockToggled) -> None:

        self.query_one(FileExplorer).shift_ui_for_taskbar(event.dock)
        self.query_one(ExplorerPathBar).shift_ui_for_taskbar(event.dock)
        self.query_one(StartMenu).shift_ui_for_taskbar(event.dock)

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

    async def on_click(self, event: events.Click):

        start_menu = self.query_one(StartMenu)
        if not start_menu.state:
            return
        if event.widget:
            if (
                event.widget is not self.query_one(StartMenu)
                and event.widget is not self.query_one(TaskBar).query_one("#start_button")
                and event.widget not in start_menu.query().results()
            ):
                await self.run_action("toggle_startmenu")

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

    @on(StartMenu.AppSelected)
    def app_selected(self, event: StartMenu.AppSelected) -> None:
        """Handle app selection from various sources."""

        def get_lowest_available_number(used_numbers: set[int]) -> int:
            i = 1
            while i in used_numbers:
                i += 1
            return i

        self.log(f"App selected: {event.app_id}")
        registered_apps = self.app.query_one(RegisteredApps)

        AppClass = registered_apps[event.app_id]
        self.log(f"Mounting app with display name: {AppClass.APP_NAME}")

        instance_counter = self.app.query_one(AppInstanceCounter)
        try:
            current_set = instance_counter[event.app_id]
        except KeyError:
            instance_counter[event.app_id] = set()
            current_set = instance_counter[event.app_id]

        lowest_available_number = get_lowest_available_number(current_set)
        current_set.add(lowest_available_number)

        if lowest_available_number == 1:
            app_id = f"{event.app_id}"
        else:
            app_id = f"{event.app_id}_{lowest_available_number}"

        self.log.debug(f"Creating new app instance with ID: {app_id}")
        main_desktop = self.query_one("#main_desktop")
        main_desktop.mount(AppClass(id=app_id, instance_number=lowest_available_number))

    @on(TermDApp.Closed)
    def termd_app_closed(self, event: TermDApp.Closed) -> None:
        """Handle the closing of a TermD App (aka a window)."""

        termdapp = cast(TermDApp, event.window)
        assert termdapp.APP_ID, f"{termdapp} does not have an APP_ID set."
        instance_counter = self.app.query_one(AppInstanceCounter)
        current_set = instance_counter[termdapp.APP_ID]
        current_set.remove(termdapp.instance_number)

        self.log.debug(
            f"App closed - ID: {termdapp.APP_ID} \n"
            f"Instance Number: {termdapp.instance_number}  \n"
            f"Current Set: {current_set}"
        )


class DataWidgetsContainer(Container):

    def __init__(self) -> None:
        super().__init__(id="datawidgets_container")
        self.display = False

    def __rich_repr__(self) -> rich.repr.Result:
        # children = self.query_children().results()
        yield "DataWidgets Container"
        # for child in children:
        #     yield child.__rich_repr__() if hasattr(child, "__rich_repr__") else repr(child)


class TermDesktop(App[None]):

    TITLE = "Term-Desktop"
    CSS_PATH = "styles.tcss"

    SCREENS = {
        "main": MainScreen,
    }

    BINDINGS = [
        Binding("f12", "log_debug_readout", "Log app debug readout to dev console", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.path_changed_signal: Signal[Path] = Signal(self, "path-changed")
        self.app_loader = AppLoader()
        # self.loader = AppLoader([Path_instance, Path_instance])   # or specify additional directories

    def compose(self) -> ComposeResult:

        ##############################
        ### INVISIBLE DATA WIDGETS ###
        ##############################
        with DataWidgetsContainer():
            yield CurrentPath()
            yield RegisteredApps()
            yield AppInstanceCounter()

        # These 'data widgets' all have display set to False, and have no compose methods.
        # They could actually be placed into a screen if I wanted to, they will effectively
        # be hidden background components whereever they are mounted.
        # But in this case I do actually want them on the App class itself and not
        # on the main screen so that they are easily queryable from anywhere in the app.

    async def on_mount(self) -> None:
        self.push_screen("main")
        self.call_after_refresh(self.load_apps)

    # * called by on_mount, above
    def load_apps(self):

        incoming_registered_apps = self.app_loader.discover_apps()
        registered_apps = self.query_one(RegisteredApps)
        registered_apps.update(incoming_registered_apps)

        main_screen = self.get_screen("main", MainScreen)  # type: ignore ( BUG IN TEXTUAL )
        main_screen.query_one(StartMenu).load_registered_apps(registered_apps)

    def action_log_debug_readout(self) -> None:

        self.log.debug(Rule("Debug Readout"))
        self.log.debug(self.screen_stack)
        # This shows all top-level children attached to the app class:
        children = self.query_children().results()
        for child in children:
            self.log.debug(child.tree)

        # This shows all screens and everything else:
        self.log(self.tree)
        self.log.debug(Rule("End of Debug Readout"))


####################
# ~ Run function ~ #
####################


def run():
    TermDesktop().run()
