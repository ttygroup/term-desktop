"starmenu.py - A start menu for the SSH Desktop application."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # from term_desktop.main import TermDesktop
    from term_desktop.screens import MainScreen
    from term_desktop.app_sdk.appbase import TDEAppBase


# Textual imports
from textual import on  # , work
from textual.app import ComposeResult
from textual.geometry import Offset
from textual.widgets import OptionList
from textual.widgets.option_list import Option

# from textual.message import Message

# Textual library imports
from textual_slidecontainer import SlideContainer

# Local imports
from term_desktop.services import ServicesManager


class StartMenu(SlideContainer):

    def __init__(self) -> None:
        super().__init__(
            slide_direction="down",
            dock_position="bottomleft",
            start_open=False,
            id="start_menu_container",
            fade=True,
            duration=0.4,
        )

        self.registered_apps: dict[str, type[TDEAppBase]] = {}
        self.taskbar_offset = Offset(0, -1)

    def compose(self) -> ComposeResult:
        option_list = OptionList(id="start_menu_list")
        option_list.can_focus = False  # Disable focus until slide is completed
        yield option_list

    def on_mount(self) -> None:
        services = self.app.query_one(ServicesManager)
        self.registered_apps = services.app_loader.registered_apps
        self.load_registered_apps(self.registered_apps)

    def load_registered_apps(self, registered_apps: dict[str, type[TDEAppBase]]) -> None:
        self.log.debug("Loading registered apps into start menu.")

        options = [Option(f"{value.APP_NAME}\n", key) for key, value in registered_apps.items()]
        self.query_one(OptionList).add_options(options)

    #####################
    # ~ Runtime stuff ~ #
    #####################

    @on(OptionList.OptionSelected)
    async def option_selected(self, event: OptionList.OptionSelected) -> None:

        if event.option_id:
            tde_app_type = self.registered_apps.get(event.option_id)
            if tde_app_type:
                self.log.debug(f"Launching app: {tde_app_type.APP_NAME} ({event.option_id})")
                services = self.app.query_one(ServicesManager)

                # This will get made into a sync method with a worker in the future
                # so that this calling method does not need to await this call.
                await services.app_service.request_process_launch(tde_app_type)
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
    async def _slide_open(self) -> None:

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
        """Called by [term_desktop.screens.mainscreen.MainScreen.taskbar_dock_toggled]"""
        jump_clicker: type[MainScreen]  # noqa: F842 # type: ignore

        if dock == "top":
            self.taskbar_offset = Offset(0, 0)
        elif dock == "bottom":
            self.taskbar_offset = Offset(0, -1)
        else:
            self.log.error(f"Unknown dock position: {dock}")
