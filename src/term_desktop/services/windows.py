"process_manager.py - The process manager for handling processes in TDE."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Awaitable, cast  # , Any
if TYPE_CHECKING:
    from term_desktop.services.manager import ServicesManager
    from term_desktop.app_sdk import TDEMainWidget, DefaultWindowSettings, CustomWindowMounts

# Textual imports
from textual import log
from textual.widget import Widget

# Textual library imports
from textual_window import window_manager, Window
from textual_window.window import WindowStylesDict

# Local imports
from term_desktop.services.servicebase import BaseService


class WindowService(BaseService):

    #####################
    # ~ Initialzation ~ #
    #####################

    def __init__(
        self,
        services_manager: ServicesManager,
    ) -> None:
        """
        Initialize the Window Manager Service.
        Note that this is a wrapper around the included window manager from the
        Textual-Window library.

        All of the core window functionality is handled by the Textual-Window library,
        including the window manager and the window class. This service is a wrapper
        around the Textual-Window library's window manager, providing a more TDE-specific
        interface for managing windows in the Term Desktop Environment.

        Windows register themselves automatically with the window manager when they are mounted.
        The window_manager instance, imported from the Textual-Window library, is a singleton
        that is attached to all windows and the Taskbar. Being designed as a plugin, it works
        independently under the hood. By wrapping the window_manager in this service, we can
        bridge to all the important stuff that we want to do with windows in TDE.
        """
        super().__init__(services_manager)
        self.window_manager = window_manager

    ####################
    # ~ External API ~ #
    ####################
    # This section is for methods that might need to be accessed by
    # anything else in TDE, including other services.

    async def start(self) -> bool:
        log("Starting Window service")
        # nothing to do here yet
        return True

    async def stop(self) -> bool:
        log("Stopping Window service")
        # nothing to do here yet
        return True

    def register_mounting_callback(
        self,
        callback: Callable[[Window], Awaitable[None]],
        callback_id: str,
    ) -> None:
        """This is used by the main screen to register a callback that will be called
        when a window is mounted.
        """
        # Wrapper around the window manager's register_mounting_callback method in
        # the Textual-Window library.
        self.window_manager.register_mounting_callback(callback, callback_id)

    async def create_new_window(
        self,
        content_instance: TDEMainWidget,
        process_id: str,
        window_dict: DefaultWindowSettings,
        styles_dict: WindowStylesDict,
        custom_mounts: CustomWindowMounts,
        callback_id: str,
    ) -> None:
        """Pass in all the ingredients to mount a window in the window manager, using the
        desired callback ID (which was set using the register_mounting_callback method).

        This is used by the ProcessManager to mount windows for apps that are launched.
        """
        # For the forseeable future, there will only be one callback ID, which is the
        # main screen's callback for the desktop. But this system is based on the
        # Textual-Window library, which is designed to work as a plugin and thus
        # be flexible enough to support multiple callback IDs in the future.

        log(f"Creating new window attached to process ID '{process_id}'.")

        new_window = Window(
            content_instance,
            id=process_id,
            styles_dict=styles_dict,
            **window_dict,
        )
        await self.window_manager.mount_window(new_window, callback_id)
        # NOTE: Mounted windows will register themselves with the window manager automatically.
        # The widget ID will be the process ID. That means we can use the inner window
        # manager to get the window by process ID later on.

        for mount_point, MountWidget in custom_mounts.items():
            mount_widget_def = cast(type[Widget], MountWidget)
            mount_widget = mount_widget_def()
            assert isinstance(mount_widget, Widget)
            if mount_point == "above_topbar":
                new_window.mount(mount_widget, before="TopBar")
            elif mount_point == "below_topbar":
                new_window.mount(mount_widget, after="TopBar")
            elif mount_point == "left_pane":
                new_window.mount(mount_widget, before="#content_pane")
            elif mount_point == "right_pane":
                new_window.mount(mount_widget, after="#content_pane")
            elif mount_point == "above_bottombar":
                new_window.mount(mount_widget, before="BottomBar")
            elif mount_point == "below_bottombar":
                new_window.mount(mount_widget, after="BottomBar")
            else:
                raise ValueError(f"Invalid mount point '{mount_point}'.")

        content_instance.post_initialized(new_window)

    def get_window_by_process_id(self, process_id: int | str) -> Window:
        """Get the current window for a given process ID.
        This will only work if the process ID has an associated window.

        Args:
            process_id: The ID of the window to retrieve.
        Returns:
            Window: The window object with the specified ID.
        Raises:
            ValueError: If the window cannot be found or if the process ID is invalid.
        """
        try:
            process_id = str(process_id)  # Ensure process_id is a string
        except Exception as e:
            raise ValueError(
                f"Invalid process ID '{process_id}'. Process ID must be an integer "
                "or a string that can be converted to an integer."
            ) from e

        windows_dict = self.window_manager.get_windows_as_dict()
        try:
            window = windows_dict[process_id]
        except KeyError as e:
            raise ValueError(f"Window with process ID '{process_id}' not found in the window manager.") from e
        else:
            return window

    # ? This is not yet used by anything yet in TDE land.
    def remove_window(self, window: Window | str) -> None:
        """Unmount a given window and remove it from the window manager.

        Args:
            window: The window to remove. Can be a Window object or the ID of the window.
        Raises:
            KeyError: If the window ID is not found in the window manager.
            ValueError: If the window is not found in the window manager.
        """
        assert isinstance(window, Window) or isinstance(
            window, str
        ), "window must be a Window object or a string representing the window ID."

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
