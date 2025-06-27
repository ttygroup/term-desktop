"""Core components and GUI elements sub-package for TDE.
This sub-package deals with core GUI components of the TDE desktop environment,
meaning the visual elements that people interact with directly.

Not the same as Services, which have their own sub-package."""

from term_desktop.core.start import StartMenu
from term_desktop.core.taskbar import TaskBar
from term_desktop.core.desktop import Desktop
from term_desktop.core.explorer import FileExplorer, ExplorerPathBar
from term_desktop.core.appchooser import AppChooser

__all__ = [
    "StartMenu",
    "TaskBar",
    "Desktop",
    "FileExplorer",
    "ExplorerPathBar",
    "AppChooser",
]
