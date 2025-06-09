"explorer.py - A file explorer for the SSH Desktop application."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from textual.widgets.directory_tree import DirEntry

# Textual imports
from textual import on  # , work
from textual.widgets import Static, DirectoryTree, Button
from textual.containers import Vertical

# Textual library imports
from textual_slidecontainer import SlideContainer

# Local imports
from term_desktop.common import CurrentPath

class FileExplorer(SlideContainer):

    def __init__(self):
        super().__init__(
            slide_direction="left",
            start_open=False,
            id="file_explorer",
            duration=0.4,
        )

    def compose(self):

        # with Vertical(id="explorer_container"):
        yield Static("File Explorer", id="explorer_title")
        self.dir_tree = DirectoryTree(
            "/home/devuser/workspace/vscode-projects/",
            id="my_tree",
        )
        yield self.dir_tree
        self.dir_tree.border_title = "Explorer"

        with Vertical(id="explorer_info"):
            yield Static("Hello, Textual!", id="my_static")
            yield Button("Close", id="close_button")

    @on(Button.Pressed, "#close_button")
    def close_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the close button press event."""
        self.state = False

    @on(DirectoryTree.FileSelected)
    def file_selected(self, event: DirectoryTree.FileSelected) -> None:

        if event.node.data:
            path = event.node.data.path
            self.log(path)
            self.app.query_one(CurrentPath).path = path

    @on(DirectoryTree.DirectorySelected)
    def node_selected(self, event: DirectoryTree.NodeExpanded[DirEntry]) -> None:
        self.log("Detected directory selection")

        if event.node.data:
            path = event.node.data.path
            self.log(path)
            self.app.query_one(CurrentPath).path = path
