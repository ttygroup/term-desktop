"windows.py - The window service for handling windows in TDE."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Awaitable, cast, TypedDict  # , Any
import asyncio

if TYPE_CHECKING:
    from term_desktop.aceofbase import ProcessContext
    from term_desktop.services.servicesmanager import ServicesManager
    from term_desktop.app_sdk import DefaultWindowSettings, CustomWindowMounts

# Textual imports
from textual.widget import Widget
from textual.worker import WorkerError

# Textual library imports
from textual_window import window_manager, Window
from textual_window.window import WindowStylesDict
from term_desktop.windows.windowbase import TDEWindowBase, TDEWindow

# Local imports
from term_desktop.services.servicebase import TDEServiceBase
from term_desktop.app_sdk import TDEMainWidget
from term_desktop.aceofbase import ProcessType


class WindowService(TDEServiceBase[TDEWindowBase]):

    class WindowMeta(TypedDict):
        """WorkerMeta is required to run work on the ServicesManager.

        Required keys:
        - content_instance: TDEMainWidget
        - process_id: str
        - window_dict: DefaultWindowSettings
        - styles_dict: WindowStylesDict
        - custom_mounts: CustomWindowMounts
        - callback_id: str
        """

        content_instance: TDEMainWidget
        app_process_id: str
        window_dict: DefaultWindowSettings
        styles_dict: WindowStylesDict
        custom_mounts: CustomWindowMounts
        callback_id: str

    #####################
    # ~ Initialzation ~ #
    #####################

    SERVICE_ID = "window_service"

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
        self.validate()
        self.window_manager = window_manager
        # NOTE: the window_manager stores the registered mounting callbacks.
        # as well as its own internal list of windows.

        self.win_unreg_signal = window_manager.signal_window_unregistered
        self.win_unreg_signal.subscribe(self._window_unregistered)
        self.win_unreg_signal.log = self.log  # type: ignore
        self._window_instance_dict: dict[str, TDEWindow] = {}
        self._window_meta_dict: dict[str, WindowService.WindowMeta] = {}

    ################
    # ~ Messages ~ #
    ################
    # None yet

    ################
    # ~ Contract ~ #
    ################

    async def start(self) -> bool:
        self.log("Starting Window service")
        # nothing to do here yet
        return True

    async def stop(self) -> bool:
        self.log("Stopping Window service")
        # nothing to do here yet
        return True

    ####################
    # ~ External API ~ #
    ####################
    # Methods that might need to be accessed by
    # anything else in TDE, including other services.

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

    def get_window_by_process_id(self, window_process_id: int | str) -> TDEWindow:
        """Get the current window for a given window process ID.
        Every app can use `self.window_process_id` to get its own process ID,
        and then use this method to retrieve the window associated with that process ID.
        (NOTE: Not the same as `self.process_id`, which is the associated app's process ID.)

        This is mostly here to allow apps to retrieve their own window, which
        will be necessary if the app has attached custom window mounts
        that it needs to interact with (ie a menu bar, command bar, etc).

        Args:
            window_process_id: The ID of the window to retrieve.
        Returns:
            Window: The window object with the specified ID.
        Raises:
            ValueError: If the window cannot be found or if the process ID is invalid.
        """
        try:
            window_process_id = str(window_process_id)  # Ensure window_process_id is a string
        except Exception as e:
            raise ValueError(
                f"Invalid process ID '{window_process_id}'. Process ID must be an integer "
                "or a string that can be converted to an integer."
            ) from e

        windows_dict = self.window_manager.get_windows_as_dict()
        try:
            window = windows_dict[window_process_id]
        except KeyError as e:
            raise ValueError(
                f"Window with process ID '{window_process_id}' not found in the window manager."
            ) from e
        else:
            return cast(TDEWindow, window)
            # NOTE: The inner manager says it returns a Window, but we know it'll be a TDEWindow.

    async def request_new_window(self, window_meta: WindowMeta) -> None:
        """Pass in all the ingredients to mount a window in the window manager, using the
        desired callback ID (which was set using the register_mounting_callback method).

        This is used by the AppService to mount windows for apps that are launched.
        """
        # For the forseeable future, there will only be one callback ID, which is the
        # main screen's callback for the desktop. I can't imagine why this might
        # need another callback ID, but its possible nevertheless.

        # Stage 0: Validate
        content_instance = window_meta["content_instance"]
        callback_id = window_meta["callback_id"]

        if not isinstance(content_instance, TDEMainWidget):  # type: ignore[unused-ignore]
            self.log.error(
                f"Invalid app class: {content_instance.__name__} is not a subclass of TDEMainWidget"
            )
            raise TypeError(f"{content_instance.__name__} is not a valid TDEMainWidget subclass")
        if callback_id not in self.window_manager.mounting_callbacks:
            raise ValueError(
                f"Callback ID '{callback_id}' is not registered in the window manager."
            )

        asyncio.create_task(self._mount_window_runner(window_meta))

    ################
    # ~ Internal ~ #
    ################
    # These should be marked with a leading underscore.

    async def _mount_window_runner(self, window_meta: WindowMeta) -> None:

        assert self.SERVICE_ID is not None
        worker_meta: ServicesManager.WorkerMeta = {
            "work": self._mount_window,
            "name": f"MountWindowWorker-{window_meta['app_process_id']}",
            "service_id": self.SERVICE_ID,
            "group": self.SERVICE_ID,
            "description": f"Mount window {window_meta['app_process_id']} using registered callback.",
            "exit_on_error": False,
            "start": True,
            "exclusive": True,  # only 1 screen push allowed at a time
            "thread": False,
        }
        worker = self.run_worker(window_meta, worker_meta=worker_meta)
        try:
            await worker.wait()
        except WorkerError:
            self.log.error(f"Failed to mount window {window_meta['app_process_id']}")

    async def _mount_window(self, window_meta: WindowMeta) -> None:
        """
        Push a screen using the registered callback. This is the callback
        that was registered with the `register_pushing_callback` method.

        Args:
            TDE_Window (TDEAppBase): The screen class to push.
            Note that this is a class definition, not an instance.
        Raises:
            ValueError: If the callback ID is not registered in the window manager.
        """

        content_instance = window_meta["content_instance"]
        app_process_id = window_meta["app_process_id"]
        window_dict = window_meta["window_dict"]
        styles_dict = window_meta["styles_dict"]
        custom_mounts = window_meta["custom_mounts"]
        callback_id = window_meta["callback_id"]

        self.log.debug(f"Creating new window attached to process ID '{app_process_id}'.")

        # Stage 1: Set available window process ID using the app's process ID.
        instance_num = self._get_available_instance_num(f"{app_process_id}-window")
        if instance_num == 1:
            window_process_id = f"{app_process_id}-window"
        else:
            window_process_id = f"{app_process_id}-window_{instance_num}"

        content_instance.set_window_process_id(window_process_id, self)

        # Stage 2: Create a new window process instance
        window_process = TDEWindowBase(
            app_process_id=app_process_id,
            window_process_id=window_process_id,
            instance_num=instance_num,
        )

        # Stage 3: Add the window process to the process dictionary
        try:
            self._add_process_to_dict(window_process, window_process_id)
        except RuntimeError as e:
            raise RuntimeError(
                f"Failed to add process {window_process_id} for window {window_process_id}. "
                "This might be due to a duplicate process ID."
            ) from e
        else:
            # If successful, store the window meta in the internal dictionary
            self._window_meta_dict[window_process_id] = window_meta

        # Stage 4: Create the window context dictionary
        window_context: ProcessContext = {
            "process_type": ProcessType.WINDOW,
            "process_id": app_process_id,
            "process_uid": window_process.uid,
            "services": self.services_manager,
        }

        # Stage 5: Get TDEwindow class and create instance from process instance
        # This is 100% internal, no reason this should fail.
        tde_window = window_process.get_window()

        # Stage 6: Create the new window instance
        try:
            window_instance = tde_window(
                content_instance=content_instance,
                styles_dict=styles_dict,
                process_context=window_context,
                window_id=window_process_id,
                window_dict=window_dict,
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to create window instance for process ID '{app_process_id}' with "
                f"window ID '{window_process_id}'."
            ) from e

        # Stage 7: Mount the window using the window manager
        try:
            await self.window_manager.mount_window(window_instance, callback_id)
        except Exception as e:
            raise RuntimeError(
                f"Failed to mount window '{window_process_id}' with callback ID '{callback_id}': {e}"
            ) from e
        # NOTE: Mounted windows will register themselves with the window manager automatically.
        # The window widget's ID (to textual) will be the window process ID.
        # The 'inner' window manager (from the textual-window library) uses the normal
        # Textual widget ID to track the windows, which is why we want to set the
        # 'widget ID' to match the window process ID.

        # Stage 8: Add any custom mounts to the new window instance
        # This has to go after the window has already been mounted or it would fail.
        for mount_point, MountWidget in custom_mounts.items():
            mount_widget_def = cast(type[Widget], MountWidget)
            mount_widget = mount_widget_def()
            assert isinstance(mount_widget, Widget)
            if mount_point == "above_topbar":
                window_instance.mount(mount_widget, before="TopBar")
            elif mount_point == "below_topbar":
                window_instance.mount(mount_widget, after="TopBar")
            elif mount_point == "left_pane":
                window_instance.mount(mount_widget, before="#content_pane")
            elif mount_point == "right_pane":
                window_instance.mount(mount_widget, after="#content_pane")
            elif mount_point == "above_bottombar":
                window_instance.mount(mount_widget, before="BottomBar")
            elif mount_point == "below_bottombar":
                window_instance.mount(mount_widget, after="BottomBar")
            else:
                raise ValueError(f"Invalid mount point '{mount_point}'.")

        # Stage 9: Store the window instance in the dictionary
        self._window_instance_dict[window_process_id] = window_instance

        # NOTE: Windows also do not need to be told to post an initialized message.
        # They already do it automatically when they are mounted.

    def _window_unregistered(self, window: Window) -> None:
        """Callback for when a window is unregistered from the window manager.
        This is used to remove the window instance from the internal dictionary.
        """
        if not isinstance(window, TDEWindow):
            self.log.warning(f"Unregistered window is not a TDEWindow: {window}")
            # return
            raise Exception(f"Unregistered window is not a TDEWindow: {window}")

        window_process_id = window.window_process_id

        app_process_id = self._window_meta_dict[window_process_id]["app_process_id"]

        try:
            self._remove_process(window_process_id)
            del self._window_instance_dict[window_process_id]
        except KeyError as e:
            self.log.error(f"Failed to remove window process '{window_process_id}': {e}")
            raise e
        else:
            self.log.debug(
                f"Removed window instance with ID '{window_process_id}' from window processes."
            )

            # Only shutdown the app process if removing the window was successful.
            self.services_manager.app_service.shutdown_app(app_process_id)

    # def win_unreg_signal_error(
    #     self,
    #     subscriber: Any,
    #     callback: Union[Callable[[SignalT], None], Callable[[SignalT], Awaitable[Any]]],
    #     error: Exception,
    # ) -> None:
    #     """Override this to handle errors differently. This will also override the `error_raising` flag.

    #     Args:
    #         subscriber: The subscriber that raised the error.
    #         callback: The callback that raised the error.
    #         error: The exception that was raised.
    #     """

    #     self.log(f"Error in callback for {subscriber}: {error}")
    #     if self._error_raising:
    #         raise SignalError(f"Error in callback {callback} for subscriber {subscriber}: {error}") from error
