"explorer.py - A file explorer for the SSH Desktop application."

# python standard library imports
from __future__ import annotations
# from typing import TYPE_CHECKING, cast
from pathlib import Path
import os
import datetime

# if TYPE_CHECKING:
from textual.widgets.directory_tree import DirEntry

# Textual imports
from textual import on, work, events
from textual.app import ComposeResult
from textual.timer import Timer
from textual.widgets import Static, DirectoryTree, Input, Tree, Button
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual.widgets._tree import TreeNode #, _TreeLine  # type: ignore[unused-ignore]

# Textual library imports
from textual_slidecontainer import SlideContainer

# Local imports
# from term_desktop.common import SimpleButton


class ExplorerPathBar(SlideContainer):
    """A container for the file explorer path bar."""

    def __init__(self):
        super().__init__(
            slide_direction="down",
            start_open=False,
            duration=0.0,
        )

    def compose(self):

        path_input = Input(classes="-textual-compact")
        path_input.compact = True
        yield path_input

    def update_path(self, path: Path) -> None:
        path_input = self.query_one(Input)
        path_input.value = str(path)

    def shift_ui_for_taskbar(self, dock: str) -> None:

        if dock == "top":
            self.styles.height = 1
        elif dock == "bottom":
            self.styles.height = 2
        else:
            self.log.error(f"Unknown dock position: {dock}")


class InfoItem(Horizontal):
    """A horizontal container for a single piece of file information."""

    def __init__(self, id: str, label: str | None = None):
        super().__init__(id=id)
        self.label = label

    def compose(self) -> ComposeResult:

        if self.label:
            yield Static(self.label)
        yield Static(id="value")

    def update(self, value: str) -> None:

        value_widget = self.query_one("#value", Static)
        value_widget.update(value)


class ExplorerInfo(Container):
    """A container for the file explorer information."""

    def __init__(self, explorer: FileExplorer):
        super().__init__()
        self.explorer = explorer

    def compose(self):

        yield InfoItem(id="name", label="Name: ")
        yield InfoItem(id="extension", label="Extension: ")
        yield InfoItem(id="size", label="Size: ")
        yield InfoItem(id="file_count", label="Total Files: ")
        yield Static("Last Modified:")
        yield InfoItem(id="last_modified")
        yield InfoItem(id="permissions", label="Permissions: ")

    @work(group="update_info", exclusive=True, exit_on_error=False)
    async def update_info(self, info_dict: dict[str, str]) -> None:

        if info_dict["type"] == "Directory":
            self.query_one("#file_count", InfoItem).display = True
            self.query_one("#extension", InfoItem).display = False
        elif info_dict["type"] == "File":
            self.query_one("#file_count", InfoItem).display = False
            self.query_one("#extension", InfoItem).display = True

        for key, value in info_dict.items():
            if key != "type":
                info_item = self.query_one(f"#{key}", InfoItem)
                info_item.update(value)


class CustomDirectoryTree(DirectoryTree):

    BINDINGS = [
        Binding("enter", "select_cursor_keypress", "Select", show=False)
    ]

    def __init__(self, path: str | Path):
        super().__init__(path=path)
        self.debounce_timer: Timer | None = None
    
    def remove_timer(self) -> None:
        self.debounce_timer = None

    #! OVERRIDE
    def action_select_cursor(self) -> None:
        """Cause a select event for the target node.

        Note:
            If `auto_expand` is `True` use of this action on a non-leaf node
            will cause both an expand/collapse event to occur, as well as a
            selected event.
        """

        if not self.debounce_timer:
            self.debounce_timer = self.set_timer(0.2, self.remove_timer)
            return

        if self.cursor_line < 0:
            return
        try:
            line = self._tree_lines[self.cursor_line]
        except IndexError:
            pass
        else:
            node = line.path[-1]
            self.post_message(Tree.NodeSelected(node)) 
            self.debounce_timer = None 

    # This one is the same as the original that was overridden, but
    # it is only called when the enter key is pressed.
    def action_select_cursor_keypress(self) -> None:
        """Cause a select event for the target node.

        Note:
            If `auto_expand` is `True` use of this action on a non-leaf node
            will cause both an expand/collapse event to occur, as well as a
            selected event.
        """
        if self.cursor_line < 0:
            return
        try:
            line = self._tree_lines[self.cursor_line]
        except IndexError:
            pass
        else:
            node = line.path[-1]
            self.post_message(Tree.NodeSelected(node))


class FileExplorer(SlideContainer):

    BINDINGS = [
        Binding("ctrl+s", "scan_directory", "Scan Directory", show=False),
    ]

    def __init__(self):
        super().__init__(
            slide_direction="left",
            start_open=False,
            id="file_explorer",
            duration=0.4,
        )
        self.file_or_dir_info: dict[Path, dict[str, str]] = {}  # Cache
        self.highlighted_node: TreeNode[DirEntry] | None = None

    def compose(self):

        with Vertical():
            yield Static("[$primary]File Explorer", classes="explorer_top")
            yield Static("[italic]Double-click: expand/run", classes="explorer_top")
            yield CustomDirectoryTree("/home/")
            yield ExplorerInfo(self)
            scan_button = Button("Scan Directory (ctrl+s)", id="scan_directory")
            scan_button.compact = True
            yield scan_button

    ####################
    # UI / Focus stuff #
    ####################

    def on_focus(self) -> None:
        dir_tree = self.query_one(DirectoryTree)
        dir_tree.focus()

    @on(SlideContainer.SlideCompleted)
    def slide_completed_explorer(self, event: SlideContainer.SlideCompleted) -> None:

        if event.state:
            self.query_one(DirectoryTree).focus()

    def shift_ui_for_taskbar(self, dock: str) -> None:

        vertical = self.query_one(Vertical)
        if dock == "top":
            vertical.styles.margin = (1, 0, 1, 0)
        elif dock == "bottom":
            vertical.styles.margin = (0, 0, 2, 0)
        else:
            self.log.error(f"Unknown dock position: {dock}")

    ##########################
    # File / Directory stuff #
    ##########################

    @on(DirectoryTree.DirectorySelected)
    async def node_selected(self, event: DirectoryTree.NodeExpanded[DirEntry]) -> None:

        if self.state is False or event.node.is_collapsed:
            return

        if event.node.data:
            path = event.node.data.path
            info_box = self.query_one(ExplorerInfo)

            if path in self.file_or_dir_info:
                info_dict = self.file_or_dir_info[path]
            else:
                info_dict = await self.get_info_dict(path)
                self.file_or_dir_info[path] = info_dict

            info_box.update_info(info_dict)

    @on(DirectoryTree.NodeHighlighted)
    async def node_highlighted(self, event: DirectoryTree.NodeHighlighted[DirEntry]) -> None:

        # NOTE: The main app also has its own event handler for this event
        # which is used to update the path bar.
        
        self.highlighted_node = event.node

        if event.node.data:
            path = event.node.data.path
            info_box = self.query_one(ExplorerInfo)

            if path in self.file_or_dir_info:
                info_dict = self.file_or_dir_info[path]
            else:
                info_dict = await self.get_info_dict(path)
                self.file_or_dir_info[path] = info_dict

            info_box.update_info(info_dict)

    @on(Button.Pressed)
    @work(group="scan_directory", exclusive=False, exit_on_error=False)
    async def action_scan_directory(self) -> None:

        if self.highlighted_node is None or \
        not self.highlighted_node.data or \
        not self.highlighted_node.data.path.is_dir():
            return
        
        current_highlighted_node = self.highlighted_node   # store this for comparison
        path = self.highlighted_node.data.path
        info_dict = self.file_or_dir_info[path]  #  get existing info
        info_dict["size"] = "Scanning..."
        info_dict["file_count"] = "Scanning..."

        info_box = self.query_one(ExplorerInfo)
        info_box.update_info(info_dict) #  updates with the scanning labels

        size_worker = self.get_directory_size(path)
        total_size, file_count = await size_worker.wait()
        formatted_size = self.format_size(total_size)

        info_dict["size"] = formatted_size
        info_dict["file_count"] = str(file_count)

        # check node we just did work on is still highlighted
        if self.highlighted_node != current_highlighted_node:
            self.log.debug("Highlighted node changed during scan, not updating info box.")
            return
        
        info_box.update_info(info_dict)        


    def format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    @work(thread=True, group="get_directory_size", exclusive=True, exit_on_error=False)
    def get_directory_size(self, path: Path) -> tuple[int, int]:

        total_size = 0
        file_count = 0

        try:
            for item in path.rglob("*"):  # Recursively get all items
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                        file_count += 1
                    except (OSError, PermissionError):
                        # Skip files we can't access
                        pass
        except (OSError, PermissionError):
            self.log.error(f"Permission denied accessing some contents of: {path}")

        return total_size, file_count

    async def get_info_dict(self, path: Path) -> dict[str, str]:

        stat = path.stat()  # Get file stats
        extension = path.suffix or "None"  # File extension

        # File size with appropriate units
        size_bytes = stat.st_size
        size_str = self.format_size(size_bytes)

        # Timestamps (Note: creation time on Unix-like systems)
        modified_time = datetime.datetime.fromtimestamp(stat.st_mtime)
        # created_time = datetime.datetime.fromtimestamp(stat.st_ctime)
        # accessed_time = datetime.datetime.fromtimestamp(stat.st_atime)

        if path.is_file():

            info_dict: dict[str, str] = {
                "name": str(path.name),
                "type": "File",
                "extension": extension,
                "size": size_str,
                "permissions": oct(stat.st_mode)[-3:],
                "last_modified": f"{modified_time.strftime('%Y-%m-%d %H:%M:%S')}",
                # "Last Accessed": accessed_time.strftime('%Y-%m-%d %H:%M:%S'),
                # "Created/Changed": created_time.strftime('%Y-%m-%d %H:%M:%S'),
            }

        elif path.is_dir():

            info_dict: dict[str, str] = {
                "name": str(path.name),
                "type": "Directory",
                "extension": extension,
                "size": "Not Scanned",  # Placeholder until size is calculated
                "file_count": "Not Scanned",  # Placeholder until file count is calculated
                "permissions": oct(stat.st_mode)[-3:],
                "last_modified": f"{modified_time.strftime('%Y-%m-%d %H:%M:%S')}",
                # "Last Accessed": accessed_time.strftime('%Y-%m-%d %H:%M:%S'),
                # "Created/Changed": created_time.strftime('%Y-%m-%d %H:%M:%S'),
            }
        else:
            raise ValueError(
                f"Path {path} is neither a file nor a directory."
                "This shouldn't be possible but the type checker complains if this "
                "check isn't here."
            )

        return info_dict
