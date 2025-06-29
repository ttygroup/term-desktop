"explorer.py - A file explorer for the SSH Desktop application."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING, Any  # , cast
from pathlib import Path
import os
import datetime

if TYPE_CHECKING:
    from term_desktop.main import MainScreen

from textual.widgets.directory_tree import DirEntry

# Textual imports
from textual import on, work, events
from textual.app import ComposeResult

# from textual.timer import Timer
from textual.geometry import clamp  # , Size
from textual.widgets import Static, DirectoryTree, Input, Button
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual.widgets._tree import TreeNode  # , _TreeLine  # type: ignore[unused-ignore]

# Textual library imports
from textual_slidecontainer import SlideContainer

# Local imports
from term_desktop.common import SpinnerWidget


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
        jump_clicker: type[MainScreen]  # .node_highlighted()  # noqa: F842 # type: ignore

        path_input = self.query_one(Input)
        path_input.value = str(path)

    def shift_ui_for_taskbar(self, dock: str) -> None:
        jump_clicker: type[MainScreen]  # .windowbar_dock_toggled()  # noqa: F842 # type: ignore

        if dock == "top":
            self.styles.height = 1
        elif dock == "bottom":
            self.styles.height = 2
        else:
            self.log.error(f"Unknown dock position: {dock}")


class ExplorerResizeBar(Static):
    """A resize bar for the file explorer."""

    def __init__(self, explorer: FileExplorer, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.explorer = explorer
        self.min_width = 25
        self.max_width = 80
        self.tooltip = "<-- Drag to resize -->"

    def on_mouse_move(self, event: events.MouseMove) -> None:

        # App.mouse_captured refers to the widget that is currently capturing mouse events.
        if self.app.mouse_captured == self:

            # Get the absolute position of the mouse right now (event.screen_offset),
            # minus where it was when the mouse was pressed down (position_on_down).
            # This gives the total delta from the original position.
            # (Note that this is not the same as the event.delta attribute,
            # that only gives you the delta from the last mouse move event.)
            total_delta = event.screen_offset - self.position_on_down

            # Once we have that, add the total delta to size of the explorer on mouse down:
            new_size = self.size_on_down + total_delta

            # negative values decrease size, positive values increase it
            self.explorer.styles.width = clamp(new_size.width, self.min_width, self.max_width)

    def on_mouse_down(self, event: events.MouseDown) -> None:

        if event.button == 1:  # left button
            self.position_on_down = event.screen_offset
            self.size_on_down = self.explorer.size

            self.add_class("pressed")
            self.capture_mouse()

    def on_mouse_up(self) -> None:

        self.remove_class("pressed")
        self.release_mouse()


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
        jump_clicker: type[ExplorerInfo]  # .update_info()  # noqa: F842 # type: ignore

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
        jump_clicker: type[FileExplorer]  # noqa: F842 # type: ignore
        # ? called by the methods: [node_selected, node_highlighted, action_scan_directory]

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

    def __init__(self, path: str | Path = "/", **kwargs: Any) -> None:
        super().__init__(path, **kwargs)
        self.visible = False

    async def _on_click(self, event: events.Click):
        if event.chain == 1:
            # single click: prevent default behavior, don't select
            event.prevent_default()
            # get currently highlighted line, return -1 if nothing is highlighted:
            line = event.style.meta.get("line", -1)
            # if the line is greater than -1, it means a line was clicked
            if line > -1:
                self.cursor_line = line  #   highlights the line that was clicked
                self.hover_line = line


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

        with Horizontal():
            with Vertical():
                yield Static("[$primary]File Explorer", classes="explorer_top")
                yield Static("[italic]Double-click: expand/run", classes="explorer_top")
                yield CustomDirectoryTree("/")
                yield ExplorerInfo(self)
                scan_button = Button("Scan Directory (ctrl+s)", id="scan_directory")
                scan_button.compact = True
                yield scan_button
                scan_spinner = SpinnerWidget(text="Scanning...", id="scan_spinner", mount_running=False)
                scan_spinner.display = False
                yield scan_spinner
            yield ExplorerResizeBar(self)

    ####################
    # UI / Focus stuff #
    ####################

    #! OVERRIDE
    def toggle(self) -> None:
        "Toggle the state of the container. Opens or closes the container."
        if not self.state:
            self.query_one(CustomDirectoryTree).visible = True
            self.state = True
        else:
            self.state = False

    def on_focus(self) -> None:
        dir_tree = self.query_one(DirectoryTree)
        dir_tree.focus()

    @on(SlideContainer.SlideCompleted)
    def slide_completed_explorer(self, event: SlideContainer.SlideCompleted) -> None:

        if event.state:
            self.query_one(DirectoryTree).focus()
        else:
            self.query_one(CustomDirectoryTree).visible = False

    def shift_ui_for_taskbar(self, dock: str) -> None:
        jump_clicker: type[MainScreen]  # .windowbar_dock_toggled()  # noqa: F842 # type: ignore

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
                info_dict = await self.make_info_dict(path)
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
                info_dict = await self.make_info_dict(path)
                self.file_or_dir_info[path] = info_dict

            info_box.update_info(info_dict)

    @on(Button.Pressed)
    @work(group="scan_directory", exclusive=False, exit_on_error=False)
    async def action_scan_directory(self) -> None:

        if (
            self.highlighted_node is None
            or not self.highlighted_node.data
            or not self.highlighted_node.data.path.is_dir()
        ):
            return

        current_highlighted_node = self.highlighted_node  # store this for comparison
        path = self.highlighted_node.data.path
        info_dict = self.file_or_dir_info[path]  #  get existing info
        info_dict["size"] = "Scanning..."
        info_dict["file_count"] = "Scanning..."
        # self.query_one("#scan_directory", Button).disabled = True  # disable button while scanning
        # self.query_one("#scan_directory", Button).label = "Scanning..."
        self.query_one("#scan_directory", Button).display = False
        self.query_one("#scan_spinner", SpinnerWidget).resume(show=True)

        info_box = self.query_one(ExplorerInfo)
        info_box.update_info(info_dict)  #  updates with the scanning labels

        size_worker = self.get_directory_size(path)
        total_size, file_count = await size_worker.wait()
        formatted_size = self.format_size(total_size)

        info_dict["size"] = formatted_size
        info_dict["file_count"] = str(file_count)
        # self.query_one("#scan_directory", Button).disabled = False  # disable button while scanning
        # self.query_one("#scan_directory", Button).label = "Scan Directory (ctrl+s)"
        self.query_one("#scan_spinner", SpinnerWidget).pause(hide=True)
        self.query_one("#scan_directory", Button).display = True

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
    def get_directory_size_old(self, path: Path) -> tuple[int, int]:

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

    @work(thread=True, group="get_directory_size", exclusive=True, exit_on_error=False)
    def get_directory_size(self, path: Path) -> tuple[int, int]:

        dir_size_map: dict[Path, tuple[int, int]] = {}

        try:
            for root, dirs, files in os.walk(path, topdown=False):  # bottom-up traversal
                root_path = Path(root)
                total_size = 0
                file_count = 0

                # Count immediate files
                for file_name in files:
                    file_path = root_path / file_name
                    try:
                        size = file_path.stat().st_size
                        total_size += size
                        file_count += 1

                        self.file_or_dir_info[file_path] = {
                            "size": self.format_size(size),
                            "file_count": "1",
                            "type": "file",
                            "name": file_path.name,
                        }
                    except (OSError, PermissionError):
                        continue

                for subdir_name in dirs:
                    subdir_path = root_path / subdir_name
                    sub_size, sub_count = dir_size_map.get(subdir_path, (0, 0))
                    total_size += sub_size
                    file_count += sub_count

                dir_size_map[root_path] = (total_size, file_count)
                self.file_or_dir_info[root_path] = {
                    "size": self.format_size(total_size),
                    "file_count": str(file_count),
                    "type": "directory",
                    "name": root_path.name,
                }

        except (OSError, PermissionError):
            self.log.error(f"Permission denied accessing contents of: {path}")

        # Return only the top-level directory's info
        top_size, top_count = dir_size_map.get(path, (0, 0))
        return top_size, top_count

    async def make_info_dict(self, path: Path) -> dict[str, str]:

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
                "type": "file",
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
                "type": "directory",
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
