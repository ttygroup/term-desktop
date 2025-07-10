"shellbase.py - Base classes for TDE Shell Sessions"

from __future__ import annotations
from abc import abstractmethod
from typing import TYPE_CHECKING, Iterable #, Any

if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager
    from textual.app import ComposeResult
    # from textual.screen import Screen    
    from textual.widgets.directory_tree import DirEntry

# Textual imports
from textual import on, events  # , work
from textual.widget import Widget
from textual.message import Message
from textual.widgets import (
    DirectoryTree,
)

# from textual.binding import Binding
# from textual.widget import Widget

# Textual library imports
from textual_window import Window
from textual_window.switcher import WindowSwitcherScreen
from textual_slidecontainer import SlideContainer

#################
# Local imports #
#################
from term_desktop.aceofbase import AceOfBase, ProcessContext, ProcessType
from term_desktop.common import (
    DummyScreen,
)
from term_desktop.common.messages import (
    ToggleStartMenu,
    ToggleExplorer,
    ToggleTaskBar,
    ToggleWindowSwitcher,
)
from term_desktop.shell.desktop import Desktop

from term_desktop.shell.default.start import StartMenu
from term_desktop.shell.default.taskbar import TaskBar
from term_desktop.shell.default.explorer import FileExplorer, ExplorerPathBar
from term_desktop.shell.default.appchooser import AppChooser



class TDEShellBase(AceOfBase):

    ################
    # ~ CONTRACT ~ #
    ################

    SHELL_NAME: str | None = None
    SHELL_ID: str | None = None
    ICON: str | None = None
    DESCRIPTION: str | None = None
    SHELL_AUTHOR: str | None = None

    @abstractmethod
    def get_shell_session(self) -> type[TDEShellSession]:
        """build me"""
        ...

    ##########################
    # ~ OPTIONAL OVERRIDES ~ #
    ##########################

    # def custom_shell_settings(self) -> CustomShellSettings:
    #     """Returns the settings for the shell to be created. \n

    #     This method can be optionally overridden to provide custom shell settings.
    #     """
    #     # This returns an empty dictionary when not overridden.
    #     return {
    # 
    #     }

    #####################
    # ~ Base Messages ~ #
    #####################

    class ShellStarted(Message):
        """Posted when an shell is either started or restarted."""

        def __init__(self, shell: TDEShellBase):
            super().__init__()
            self.shell = shell

    #####################
    # ~ Backend Setup ~ #
    #####################            

    @classmethod
    def validate(cls) -> None:

        required_members = {
            "SHELL_ID": "class attribute",
            "SHELL_NAME": "class attribute",
            "SHELL_AUTHOR": "class attribute",
            "ICON": "class attribute",
            "DESCRIPTION": "class attribute",
            # more will go here as needed
        }
        cls.validate_stage1()
        cls.validate_stage2(required_members)


    async def kill(self) -> None:
        # N/I yet
        pass



class TDEShellSession(Widget):
    """Base class for all shell sessions in TDE. \n

    This is the widget that will be mounted in to the shell manager
    when a shell is launched.

    # ~ create more thorough explanation

    """

    class Initialized(Message):
        """Posted when the shell is initialized. This will bubble up to
        the shell manager and then the main screen."""

        # def __init__(self):
        #     super().__init__()

    def __init__(self, process_context: ProcessContext):
        super().__init__()
        self._process_context = process_context
        self.services.window_service.register_mounting_callback(
            self.mounting_callback,
            callback_id="main_desktop",
        )

    def compose(self) -> ComposeResult:

        self.log.debug("Composing A TDEShellSession...")

        ######################
        ### DOCKED WIDGETS ###
        # NOTE: The order these are in is important for the layout

        yield from self.make_file_explorer()
        yield from self.make_explorer_path_bar()
        yield from self.make_start_menu()
        yield from self.make_task_bar()

        ###############
        ### DESKTOP ###
        # NOTE: Windows are mounted into the Desktop container.

        yield from self.make_desktop()

    # This method is called by the window service to mount windows
    # into the shell. By default it will mount them into the main desktop.
    # Someone might want to override this to mount them into a different
    # container or to do some other logic (perhaps for a tiling manager or something).
    async def mounting_callback(self, window: Window) -> None:
        await self.query_one(Desktop).mount(window)

    # This will be called by the shell service when the shell session is initialized. 
    def post_initialized(self) -> None:
        self.post_message(self.Initialized())

    # This can be used for any initialization logic that needs to be run
    # after the shell session is mounted and ready to go
    def on_initialized(self) -> None:
        self.log.debug("Shell session initialized.")
        pass

    ##########################
    # ~ Default Components ~ #
    ##########################

    #! NOTE: These should maybe also return something under a contract
    #! instead of just yielding a widget.

    def make_file_explorer(self) -> Iterable[Widget]:
        """Returns the FileExplorer class to be used in this shell session."""
        yield FileExplorer()

    def make_explorer_path_bar(self) -> Iterable[Widget]:
        """Returns the ExplorerPathBar class to be used in this shell session."""
        yield ExplorerPathBar()

    def make_start_menu(self) -> Iterable[Widget]:
        """Returns the StartMenu class to be used in this shell session."""
        yield StartMenu(self.services)

    def make_task_bar(self) -> Iterable[Widget]:
        """Returns the TaskBar class to be used in this shell session."""
        yield TaskBar(start_open=True)

    def make_desktop(self) -> Iterable[Widget]:
        """Returns the Desktop class to be used in this shell session."""
        yield Desktop(id="main_desktop")

    def push_window_switcher(self, cycle_key: str = "f4") -> None:
        """Pushes the WindowSwitcherScreen to the app's screen stack."""
        self.app.push_screen(WindowSwitcherScreen(cycle_key=cycle_key))

    ##################
    # ~ Properties ~ #
    ################## 

    @property
    def process_type(self) -> ProcessType:
        return self._process_context["process_type"]

    @property
    def process_id(self) -> str:
        return self._process_context["process_id"]

    @property
    def process_uid(self) -> str:
        return self._process_context["process_uid"]

    @property
    def services(self) -> ServicesManager:
        return self._process_context["services"]

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
        self.push_window_switcher()

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




