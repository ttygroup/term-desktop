from textual.widget import Widget
import rich.repr
from textual.widgets import Static
from pathlib import Path


class NoSelectStatic(Static):
    """This class is used in window.py and windowbar.py to create buttons."""

    @property
    def allow_select(self) -> bool:
        return False
    
class CurrentPath(Widget):
    """A widget to display the current path."""

    def __init__(self) -> None:
        super().__init__(id="current_path")
        self.path: Path | None = None
        self.display = False

    def __rich_repr__(self) -> rich.repr.Result:
        yield str(self.path)