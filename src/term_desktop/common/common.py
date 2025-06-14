# python
from typing import Type
from pathlib import Path

# Textual
from textual.widget import Widget
from textual.widgets import Static
import rich.repr

# Local
from term_desktop.common import DictDataWidget
from term_desktop.appbase import TermDApp


class NoSelectStatic(Static):
    """This class is used in window.py and windowbar.py to create buttons."""

    @property
    def allow_select(self) -> bool:
        return False


class RegisteredApps(DictDataWidget[str, Type[TermDApp]]):
    pass


class AppInstanceCounter(DictDataWidget[str, set[int]]):
    pass


class CurrentPath(Widget):

    def __init__(self) -> None:
        super().__init__(id="current_path")
        self.path: Path | None = None
        self.display = False

    def __rich_repr__(self) -> rich.repr.Result:
        yield str(self.path)
