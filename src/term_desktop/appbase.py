"""Base class for all apps. \n"""

# Python imports
from __future__ import annotations
from typing import Callable, Optional, Any

# Textual imports
from textual.message import Message
from textual.widget import Widget

# import textual.events as events
# from textual.widget import Widget

# Textual library imports
from textual_window import Window
from textual_window.window import MODE, STARTING_HORIZONTAL, STARTING_VERTICAL


class TermDApp(Window):

    DEFAULT_CSS = """
    TermDApp {
        width: 60; height: 30;
    }  
    """

    # The following must be overridden in the app using this class:
    APP_NAME: str | None = None
    APP_ID: str | None = None

    class StartApp(Message):
        """Posted when an app is either mounted or restarted. \n

        Handled by:
            `TermDesktop.start_app`: The main app class in main.py.
        """

        def __init__(self, app: TermDApp):
            super().__init__()
            self.app = app

    def __init__(
        self,
        *children: Widget,
        id: str,
        instance_number: int,
        mode: MODE = "temporary",
        icon: str | None = None,
        classes: str | None = None,
        name: str | None = None,
        starting_horizontal: STARTING_HORIZONTAL = "center",
        starting_vertical: STARTING_VERTICAL = "middle",
        start_open: bool = False,
        start_snapped: bool = True,
        allow_resize: bool = True,
        allow_maximize: bool = False,
        menu_options: dict[str, Callable[..., Optional[Any]]] | None = None,
        animated: bool = True,
        show_title: bool = True,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            *children,
            id=id,
            mode=mode,
            icon=icon,
            classes=classes,
            name=name,
            starting_horizontal=starting_horizontal,
            starting_vertical=starting_vertical,
            start_open=start_open,
            start_snapped=start_snapped,
            allow_resize=allow_resize,
            allow_maximize=allow_maximize,
            menu_options=menu_options,
            animated=animated,
            show_title=show_title,
            disabled=disabled,
        )

        self.instance_number = instance_number

    @classmethod
    def validate_interface(cls):
        """Validates if a app class implements the required contract."""

        required_members = {
            "APP_NAME": "attribute",
            "APP_ID": "attribute",
            # more will go here as needed
        }

        for member, kind in required_members.items():
            try:
                attr = getattr(cls, member)
            except AttributeError:
                raise NotImplementedError(f"{cls.__name__} must implement {member} ({kind}).")
            else:
                if attr is None:
                    raise NotImplementedError(f"{cls.__name__} must implement {member} ({kind}).")
