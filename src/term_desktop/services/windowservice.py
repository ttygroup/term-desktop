"process_manager.py - The process manager for handling processes in TDE."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING, Callable #, Any
if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager
    from textual.screen import Screen
    # from term_desktop.app_sdk.appbase import TDEApp

# Textual imports
# from textual import log
from term_desktop.services.servicebase import BaseService

# Textual library imports
from textual_window import window_manager, Window

# Local imports
# from term_desktop.app_sdk.appbase import TDEApp


class WindowService(BaseService):

    def __init__(
        self, 
        services_manager: ServicesManager, 
    ) -> None:
        """        
        Initialize the Window Manager Service.
        Note that this is a wrapper around the included window manager from the
        Textual-Window library.
        """
        super().__init__(services_manager)
        self.window_manager = window_manager
        self.main_screen: Screen[None] | None = None
        

    async def start(self) -> bool:
        return True

    async def stop(self) -> bool:
        return True
    

    def register_mounting_callback(self, callback: Callable[[Window], None], id: str) -> None:
        """Register a callback which can be used by the Window Manager to mount windows
        that are passed into it with the `mount_window` method.
        """
        self.window_manager.register_mounting_callback(callback, id)

    def mount_window(self, window: Window, id: str) -> None:
        """Mount a window using a callback registered with the `register_mounting_callback`
        method.
        This allows the manager to handle the mounting of windows without needing to mount them
        directly into their destination. If you have a process manager of some sort that creates
        and manages windows, this allows the process manager to just send them to the window manager.
        """

        # Mounted windows will register themselves with the window manager automatically.
        self.window_manager.mount_window(window, id)

    def remove_window(self, window: Window | str) -> None:
        """Unmount a given window and remove it from the window manager.
        
        Args:
            window: The window to remove. Can be a Window object or the ID of the window.
        """
        assert (isinstance(window, Window) or isinstance(window, str)), \
            "window must be a Window object or a string representing the window ID."

        if isinstance(window, str):
            try:
                window = self.window_manager.windows[window]
            except KeyError as e:
                raise KeyError(f"Window with ID '{window}' not found in the window manager.") from e

        else:
            window_list = self.window_manager.get_windows_as_list()
            try:
                index = window_list.index(window)
                window = window_list[index]
            except ValueError as e:
                raise ValueError(f"Window '{window}' not found in the window manager.") from e
            
        # This will trigger the remove sequence. The window will unregister itself
        # from the manager automatically when this is called.
        window.remove_window()