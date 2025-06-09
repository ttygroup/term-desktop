"taskfile_widget.py"

# python standard library imports
from __future__ import annotations

# import os
from pathlib import Path

# from typing import TYPE_CHECKING

# if TYPE_CHECKING:
#     # from typing import Any, Literal
#     from textual.widgets.directory_tree import DirEntry

# Textual / rich imports
# from rich.text import Text
# from textual.screen import Screen
# from textual import on  # , work
# from textual.app import App
# from textual.widgets import Footer, Static, DirectoryTree, Button, OptionList
# from textual.containers import Horizontal, Vertical
# from textual.binding import Binding
# from textual.widget import Widget
# from textual.reactive import reactive
from textual.widgets import Static

# textual library imports
from textual_window import Window

# local imports
from term_desktop.datawidgets import CurrentPath


class TaskfileWindow(Window):

    # current_path: reactive[Path | None] = reactive(None)
    # matches: reactive[list[Path]] = reactive([])

    def __init__(self):
        super().__init__(id="taskfile_widget", name="Taskfile Runner")
        self.target_files = {"justfile", "Justfile"}
        self.current_path: Path | None = None
        self.matches: list[Path] = []

    def compose(self):

        yield Static(f"Current Folder: {self.current_path}", id="taskfile_title")
        yield Static(f"Taskfiles: {self.matches}", id="taskfile_list")

    def update_path(self, new_path: Path | None = None) -> None:
        if new_path:
            self.current_path = new_path
        else:
            self.current_path = self.app.query_one(CurrentPath).path

        if self.current_path:
            self.matches = [p for p in self.current_path.iterdir() if p.name in self.target_files]
            self.log(f"Found taskfile(s): {self.matches}")

        self.query_one("#taskfile_title", Static).update(f"Current Folder: {self.current_path}")

        matches_text = ", ".join(str(p) for p in self.matches)
        self.query_one("#taskfile_list", Static).update(f"Taskfiles: {matches_text}")

        # self.query_one("#taskfile_list", Static).update(f"Taskfiles: {self.matches}")
