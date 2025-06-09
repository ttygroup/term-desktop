"notepad.py"

# python standard library imports
from __future__ import annotations
from typing import Any
from pathlib import Path

# Textual imports
from textual.widgets import Static, Markdown, TextArea
from textual.content import Content
# from rich.text import Text

# Textual library imports
from textual_window import Window


# local imports
# from term_desktop.datawidgets import CurrentPath


class Notepad(Window):

    # current_path: reactive[Path | None] = reactive(None)
    # matches: reactive[list[Path]] = reactive([])
    DEFAULT_CSS = """
    Notepad {
        width: 60; height: 30;
    }
    """

    def __init__(self, current_path: Path | None = None, **kwargs: Any):
        super().__init__(
            id="notepad",
            start_open=True,
            icon="📝",
            starting_horizontal="centerright",
            show_maximize_button=True,
            **kwargs
        )
        self.current_path: Path | None = current_path
        self.log(f"Current path set to: {self.current_path}")

    def compose(self):

        if self.current_path:
            if self.current_path.as_posix().endswith(".md"):
                yield Markdown(self.current_path.read_text())
            else:
                yield TextArea(self.current_path.read_text())
        else:
            yield Static("No file selected. Please select a file to view its contents.")
            


    # def update_path(self, new_path: Path | None = None) -> None:
    #     if new_path:
    #         self.current_path = new_path
    #     else:
    #         self.current_path = self.app.query_one(CurrentPath).path

    #     if self.current_path:
    #         self.matches = [p for p in self.current_path.iterdir() if p.name in self.target_files]
    #         self.log(f"Found taskfile(s): {self.matches}")

    #     self.query_one("#taskfile_title", Static).update(f"Current Folder: {self.current_path}")

    #     matches_text = ", ".join(str(p) for p in self.matches)
    #     self.query_one("#taskfile_list", Static).update(f"Taskfiles: {matches_text}")

    #     # self.query_one("#taskfile_list", Static).update(f"Taskfiles: {self.matches}")
