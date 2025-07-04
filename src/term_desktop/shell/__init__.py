"""Core components and GUI elements sub-package for TDE.
This sub-package deals with core GUI components of the TDE desktop environment,
meaning the visual elements that people interact with directly.

Not the same as Services, which have their own sub-package.

Only thing this package exports is the Shell class, which represents
the core desktop environment shell.

#! Note here about modularity, shell swapping, etc.
"""

from term_desktop.shell.shellmanager import ShellManager

__all__ = [
    "ShellManager",
]
