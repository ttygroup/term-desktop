"starmenu.py - A start menu for the SSH Desktop application."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from term_desktop.main import TermDesktop

# Textual imports
from textual import on  # , work
from textual.app import ComposeResult
from textual.geometry import Offset
from textual.widgets import OptionList
from textual.widgets.option_list import Option
from textual.message import Message

# Textual library imports
from textual_slidecontainer import SlideContainer

# Local imports
from term_desktop.common import RegisteredApps


__all__ = [
    "StartMenu",
]


class StartMenu(SlideContainer):

    class AppSelected(Message):
        """Posted when an app is selected from the start menu.
        Posted by:
            `StartMenuContainer.option_selected`
        """

        def __init__(self, app_id: str):
            super().__init__()
            self.app_id = app_id
            """This will be the key of the app in the RegisteredApps widget, 
            which will correspond to the app's APP_ID attribute."""

    def __init__(self) -> None:
        super().__init__(
            slide_direction="down",
            start_open=False,
            id="start_menu_container",
            fade=True,
            duration=0.4,
        )

        self.taskbar_offset = Offset(0, -1)

    def compose(self) -> ComposeResult:
        option_list = OptionList(id="start_menu_list")
        option_list.can_focus = False  # Disable focus until slide is completed
        yield option_list

    called_by: list[TermDesktop]  # load_apps method

    def load_registered_apps(self, registered_apps: RegisteredApps) -> None:

        self.log.debug("Loading registered apps into start menu.")

        options = [Option(f"{value.APP_NAME}\n", key) for key, value in registered_apps.items()]
        self.query_one(OptionList).add_options(options)

    @on(OptionList.OptionSelected)
    async def option_selected(self, event: OptionList.OptionSelected) -> None:

        self.log.debug(f"Selected option: {event.option_id}")
        if event.option_id:
            self.post_message(self.AppSelected(event.option_id))
            self.close()

    @on(SlideContainer.SlideCompleted)
    def slide_completed_startmenu(self, event: SlideContainer.SlideCompleted) -> None:

        option_list = event.container.query_one(OptionList)
        if event.state:    
            option_list.can_focus = True
            option_list.focus()
            option_list.action_first()
        else:
            option_list.can_focus = False            
            event.container.query().blur()

    #! OVERRIDE
    def _slide_open(self) -> None:

        # This is here just in case anyone calls this method manually:
        if self.state is not True:
            self.set_reactive(SlideContainer.state, True)  # set state without calling the watcher

        def slide_open_completed() -> None:
            self.post_message(self.SlideCompleted(True, self))

        # if not self.floating:
        self.display = True
        self.animate(
            "offset",
            value=self.taskbar_offset,  # <-- This line modified from original in SlideContainer
            duration=self.duration,
            easing=self.easing_function,
            on_complete=slide_open_completed,
        )
        if self.fade:
            self.styles.animate(
                "opacity", value=1.0, duration=self.duration, easing=self.easing_function
            )  # reset to original opacity

    def shift_ui_for_taskbar(self, dock: str) -> None:

        if dock == "top":
            self.taskbar_offset = Offset(0, 0)
        elif dock == "bottom":
            self.taskbar_offset = Offset(0, -1)
        else:
            self.log.error(f"Unknown dock position: {dock}")
