"App Base class and SDK sub-package for TDE"

# WindowStylesDict is from the Textual-Window library, but we want to make
# it available as part of the TDEApp SDK for convenience.
from textual_window.window import WindowStylesDict

from term_desktop.app_sdk.appbase import (
    TDEApp,
    TDEMainWidget,
    LaunchMode,
    CustomWindowSettings,
    DefaultWindowSettings,
    CustomWindowMounts,
)

__all__ = [
    "TDEApp",
    "TDEMainWidget",
    "LaunchMode",
    "CustomWindowSettings",
    "DefaultWindowSettings",
    "CustomWindowMounts",
    "WindowStylesDict",
]
