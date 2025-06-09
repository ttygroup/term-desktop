"starmenu.py - A start menu for the SSH Desktop application."

# python standard library imports
from __future__ import annotations

# from pathlib import Path
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:

# Textual imports
from textual import on  # , work
from textual.widgets import OptionList
from textual.widgets.option_list import Option

# Textual library imports
from textual_slidecontainer import SlideContainer

# Local imports
from term_desktop.core.explorer import FileExplorer


class StartMenu(SlideContainer):

    options_dict = {
        "file_explorer": "File Explorer",
        "taskfile_runner": "TaskFile Runner [italic]justfile/makefile/more[/italic]",
        "settings": "Settings [italic]Configure your desktop[/italic]",
    }

    def __init__(self):
        super().__init__(
            slide_direction="down",
            start_open=False,
            id="start_menu",
            fade=True,
            duration=0.4,
        )
        self.options = [
            # Text.from_markup("File Explorer\n"),
            # Text.from_markup("TaskFile Runner \n[italic]justfile/makefile/more[/italic]"),
            # Text.from_markup("Settings \n[italic]Configure your desktop[/italic]"),
            Option("File Explorer\n", "file_explorer"),
            Option("TaskFile Runner\n", "taskfile_runner"),
            Option("Settings\n", "settings"),
        ]

    def compose(self):
        self.option_list = OptionList(*self.options, id="start_menu_list")
        yield self.option_list

    @on(OptionList.OptionSelected)
    async def option_selected(self, event: OptionList.OptionSelected) -> None:
        self.log(f"Selected option: {event.option_id}")

        if event.option_id == "file_explorer":
            self.app.query_one(FileExplorer).toggle()

        elif event.option_id == "taskfile_runner":
            # desktop = self.app.query_one("#main_desktop", Container)
            # taskfile_window = TaskfileWindow()
            # taskfile_window.masnager.rebuild_windows_dict()
            # await taskfile_window.manager.windowbar_build_buttons()
            # desktop.mount(TaskfileWindow())
            pass

        elif event.option_id == "settings":
            pass

        self.state = False
