"servicetemplate.py - Template for services. Replace this with description."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Awaitable

if TYPE_CHECKING:
    from term_desktop.services.manager import ServicesManager
    from term_desktop.screens import TDEScreen

# Textual imports
# from textual.message import Message

# Textual library imports
# none

# Local imports
from term_desktop.services.servicebase import TDEServiceBase
from term_desktop.screens import MainScreen, TDEScreenBase, TDEScreen


class ScreenService(TDEServiceBase):

    #####################
    # ~ Initialzation ~ #
    #####################

    def __init__(
        self,
        services_manager: ServicesManager,
    ) -> None:
        """
        Initialize the Screen service.
        """
        super().__init__(services_manager)
        #! Make these reactive dicts?

        self.mounting_callback: Callable[[TDEScreen], Awaitable[None]] | None = None
        self._screen_processes: dict[str, TDEScreen] = {}
        self._active_sreens: dict[str, TDEScreenBase] = {}

    ################
    # ~ Messages ~ #
    ################
    # None yet

    ####################
    # ~ External API ~ #
    ####################
    # This section is for methods or properties that might need to be
    # accessed by anything else in TDE, including other services.

    async def start(self) -> bool:
        """Start the Screen service. service."""

        # Example of using a worker inside of a service
        # Any extra positional and keyword arguments that not part of the
        # run_worker function will be passed to the callback function.
        # Note this is set to use thread workers by default, and so the
        # callback function should NOT be async.
        #
        # worker = self.run_worker(
        #     self._func_to_run,
        #     any_args_here,
        #     name="AppLoaderWorker",
        #     description="Discovering apps in directories",
        #     group="AppLoader",
        #     exclusive=True,
        #     keyword1 = "some_value_here",
        #     keyword2 = "another_value_here",
        # )
        # some_value = await worker.wait()

        return True

    async def stop(self) -> bool:
        return True

    def register_mounting_callback(self, callback: Callable[[TDEScreen], Awaitable[None]]) -> None:
        """This is used by the Uber App Class (TermDesktop) to register a
        callback that will be called when a new screen is mounted.

        Args:
            callback (Callable[[TDEScreen], Awaitable[None]]): The callback function to
                be called when a new screen is mounted. The callback should accept a
                single argument, which is the screen being mounted.
        Raises:
            ValueError: If a callback with the same ID is already registered.
            ValueError: If the callback is not callable.
        """
        if not callable(callback):
            raise ValueError(f"Callback {callback} is not callable.")
        self.mounting_callback = callback

    def register_dismissing_callback(self, callback: Callable[[TDEScreen], Awaitable[None]]) -> None:
        """This is used by the Uber App Class (TermDesktop) to register a
        callback that will be called when a screen is dismissed.

        Args:
            callback (Callable[[TDEScreen], Awaitable[None]]): The callback function to
                be called when a screen is dismissed. The callback should accept a
                single argument, which is the screen being dismissed.
        Raises:
            ValueError: If the callback is not callable.
        """
        if not callable(callback):
            raise ValueError(f"Callback {callback} is not callable.")
        self.dismissing_callback = callback

    async def mount_screen(
        self,
        screen: type[TDEScreenBase],
    ) -> None:
        """Mount a screen using the registered callback. This is the callback
        that was registered with the `register_mounting_callback` method.
        """
        if self.mounting_callback is None:
            raise RuntimeError("No mounting callback has been registered.")
        try:
            new_screen = screen()
        except Exception as e:
            raise RuntimeError(f"Error while creating screen '{screen.__class__.__name__}': {e}") from e
        try:
            self.mounting_callback(new_screen)
        except Exception as e:
            raise RuntimeError(
                f"Error while executing callback '{self.mounting_callback}' "
                f"for screen '{screen.__class__.__name__}': {e}"
            ) from e
        self.active_sreens[new_screen.uid] = new_screen

    async def dismiss_screen(
        self,
        screen: TDEScreen,
    ) -> None:
        """Dismiss a screen using a registered callback id. This is the callback
        that was registered with the `register_dismissing_callback` method.
        """
        if self.dismissing_callback is None:
            raise RuntimeError("No dismissing callback has been registered.")
        try:
            await self.dismissing_callback(screen)
        except Exception as e:
            raise RuntimeError(
                f"Error while executing dismissing callback '{self.dismissing_callback}' "
                f"for screen '{screen.__class__.__name__} ': {e}"
            ) from e

    def push_main_screen(self) -> None:
        """Push the main screen onto the screen stack using the registered
        mounting callback. This takes no arguments, as only 1 screen mounting
        callback is allowed to be registered at a time.

        This is currently only used by the Uber App Class (TermDesktop) to
        tell the ScreenService to push the main screen onto the screen stack.
        """
        self.run_worker(
            self.mount_screen,
            MainScreen,
            name="PushMainScreenWorker",
        )

    ################
    # ~ Internal ~ #
    ################
    # This section is for methods that are only used internally
    # These should be marked with a leading underscore.

    async def _launch_process(self, TDE_App: type[TDEAppBase]) -> None:
        """
        Args:
            TDE_App (TDEAppBase): The app to launch.
            Note that this is a class definition, not an instance.
        Raises:
            TypeError: If TDE_App is not a subclass of TDEAppBase.
            AssertionError: If the TDE_App is not valid (should never happen)
        Raises:
            RuntimeError: If a process with the given ID already exists.
        """
        self.log(f"Launching process for app: {TDE_App.APP_NAME}")

        assert issubclass(TDE_App, TDEAppBase)
        assert TDE_App.APP_NAME is not None
        assert TDE_App.APP_ID is not None

        # Get the app process ID with a number if needed.
        # This is to handle multiple instances of the same app.
        # Note that this is a simple identifier just for the App Process Service.
        # There is also a UID that is set on all types of processes in TDE.
        process_id = self._set_available_process_id(TDE_App.APP_ID)

        # * Create the app process instance
        # This is the instance of the base app inherited from the TDEAppBase class. Right now
        # it just holds all the app metadata. Store this in the process manager.
        app_process = TDE_App(process_id=process_id)
        try:
            self._add_process_to_dict(app_process, process_id)
        except RuntimeError as e:
            self.log.error(f"Failed to add process {process_id}: {e}")
            raise RuntimeError(
                f"Failed to add process {process_id} for app {TDE_App.APP_NAME}. "
                "This might be due to a duplicate process ID."
            ) from e

        app_context: ProcessContext = {
            "process_type": ProcessType.APP,
            "process_id": process_id,
            "process_uid": app_process.uid,
            "services": self.services_manager,
        }

    def _add_process_to_dict(self, tde_app_instance: TDEAppBase, process_id: str) -> None:
        """
        Add a process to the app service's process dictionary.

        Args:
            tde_app_instance (TDEAppBase): The app instance to add.
            process_id (str): The ID of the app process.
        Raises:
            RuntimeError: If a process with the given ID already exists.
        """

        if process_id in self._processes:
            raise RuntimeError(f"Process with ID {process_id} already exists.")

        self._processes[process_id] = tde_app_instance
        self.log(f"Process {tde_app_instance.APP_NAME} with ID {process_id} added.")

    def _set_available_process_id(self, APP_ID: str) -> str:

        try:
            current_set = self._instance_counter[APP_ID]  # get set if exists
        except KeyError:
            current_set: set[int] = set()  # if not, make a new set
            self._instance_counter[APP_ID] = current_set

        i = 1
        while i in current_set:
            i += 1
        current_set.add(i)
        if i == 1:
            return f"{APP_ID}"
        else:
            return f"{APP_ID}_{i}"        
