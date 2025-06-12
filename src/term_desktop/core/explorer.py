"explorer.py - A file explorer for the SSH Desktop application."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.widgets.directory_tree import DirEntry

# Textual imports
from textual import on  # , work
from textual.widgets import Static, DirectoryTree #, Button
from textual.containers import Vertical

# Textual library imports
from textual_slidecontainer import SlideContainer

# Local imports
from term_desktop.common import CurrentPath #, SimpleButton


class FileExplorer(SlideContainer):

    def __init__(self):
        super().__init__(
            slide_direction="left",
            start_open=False,
            id="file_explorer",
            duration=0.4,
        )

    def compose(self):

        yield Static("File Explorer", id="explorer_title")
        self.dir_tree = DirectoryTree(
            "/home/",
            id="explorer_tree",
        )
        yield self.dir_tree
        self.dir_tree.border_title = "Explorer"

        with Vertical(id="explorer_info"):
            yield Static("Explorer Info Here", id="explorer_info_text")

    def on_mount(self) -> None:

        # Disable all the children so that they can't be focused while the explorer is closed.
        self.query().set(disabled=True)


    def watch_state(self, old_state: bool, new_state: bool) -> None:
        if new_state == old_state:
            return
        if new_state is True:
            self.query().set(disabled=False)
            self._slide_open()
        else:
            self._slide_closed()

    @on(DirectoryTree.FileSelected)
    @on(DirectoryTree.DirectorySelected)
    def node_selected(self, event: DirectoryTree.NodeExpanded[DirEntry]) -> None:
        self.log("Detected directory selection")

        if event.node.data:
            path = event.node.data.path
            self.log(path)
            self.app.query_one(CurrentPath).path = path

    @on(SlideContainer.SlideCompleted)
    def slide_completed_explorer(self, event: SlideContainer.SlideCompleted) -> None:
        """Handle the slide completion event."""
        if event.state:
            self.query_one(DirectoryTree).focus()
        else:
            self.query().set(disabled=False)
