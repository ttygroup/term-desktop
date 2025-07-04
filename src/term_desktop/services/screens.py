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
from term_desktop.aceofbase import ProcessContext, ProcessType
from term_desktop.services.servicebase import TDEServiceBase
from term_desktop.screens import MainScreenMeta, TDEScreenBase, TDEScreen


class ScreenService(TDEServiceBase):

    #####################
    # ~ Initialzation ~ #
    #####################

    SERVICE_ID = "screen_service"

    def __init__(
        self,
        services_manager: ServicesManager,
    ) -> None:
        """
        Initialize the Screen service.
        """
        super().__init__(services_manager)
        self.validate()

        self._screen_instance_dict: dict[str, TDEScreen] = {}
        self._pushing_callback: Callable[[TDEScreen], Awaitable[None]] | None = None

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
        # nothing here yet
        return True

    async def stop(self) -> bool:
        # nothing here yet
        return True

    def push_main_screen(self) -> None:
        """Push the main screen onto the screen stack using the registered
        pushing callback. This takes no arguments, as only 1 screen pushing
        callback is allowed to be registered at a time.

        This is currently only used by the Uber App Class (TermDesktop) to
        tell the ScreenService to push the main screen onto the screen stack.
        """
        self.request_screen_push(MainScreenMeta)

    def register_pushing_callback(self, callback: Callable[[TDEScreen], Awaitable[None]]) -> None:
        """This is used by the Uber App Class (TermDesktop) to register a
        callback that will be called when a new screen is pushed.

        Args:
            callback (Callable[[TDEScreen], Awaitable[None]]): The callback function to
                be called when a new screen is pushed. The callback should accept a
                single argument, which is the screen being pushed.
        Raises:
            ValueError: If a callback with the same ID is already registered.
            ValueError: If the callback is not callable.
        """
        if not callable(callback):
            raise ValueError(f"Callback {callback} is not callable.")
        self._pushing_callback = callback

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

    def request_screen_push(
        self,
        TDE_Screen: type[TDEScreenBase],
    ) -> None:
        """
        Request the screen service to push a new screen for the given TDEScreenBase.

        Args:
            TDE_Screen (type[TDEScreenBase]): The screen class to push.
        Raises:
            TypeError: If TDE_Screen is not a subclass of TDEScreenBase.
            ValueError: If TDE_Screen has no SCREEN_ID defined.
            RuntimeError: If a process with the given ID already exists.
        """

        # Stage 0: Validate
        if not issubclass(TDE_Screen, TDEScreenBase):  # type: ignore[unused-ignore]
            self.log.error(f"Invalid app class: {TDE_Screen.__name__} is not a subclass of TDEAppBase")
            raise TypeError(f"{TDE_Screen.__name__} is not a valid TDEAppBase subclass")
        if TDE_Screen.SCREEN_ID is None:
            self.log.error(f"Invalid screen class: {TDE_Screen.__name__} has no SCREEN_ID defined.")
            raise ValueError(f"{TDE_Screen.__name__} has no SCREEN_ID defined.")

        worker_meta: ServicesManager.WorkerMeta = {
            "work": self._push_screen,
            "name": f"PushScreenWorker-{TDE_Screen.SCREEN_ID}",
            "service_id": self.SERVICE_ID,
            "group": self.SERVICE_ID,
            "description": f"Push screen {TDE_Screen.SCREEN_ID} onto the screen stack.",
            "exit_on_error": False,
            "start": True,
            "exclusive": True,  # only 1 screen push allowed at a time
            "thread": False,
        }
        self.run_worker(TDE_Screen, worker_meta=worker_meta)

    #! Not used by anything yet
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

    ################
    # ~ Internal ~ #
    ################
    # This section is for methods that are only used internally
    # These should be marked with a leading underscore.

    async def _push_screen(self, TDE_Screen: type[TDEScreenBase]) -> None:
        """
        Push a screen using the registered callback. This is the callback
        that was registered with the `register_pushing_callback` method.

        Args:
            TDE_Screen (TDEAppBase): The screen class to push.
            Note that this is a class definition, not an instance.
        Raises:
            TypeError: If TDE_Screen is not a subclass of TDEScreenBase.
            AssertionError: If the TDE_Screen is not valid (should never happen)
            RuntimeError: If a process with the given ID already exists.
        """
        self.log(f"Screen process requesting push: {TDE_Screen.SCREEN_ID}")

        # Stage 0: Validate
        if self._pushing_callback is None:
            raise RuntimeError("No pushing callback has been registered.")

        # Stage 1: Set available process ID
        assert TDE_Screen.SCREEN_ID is not None
        process_id = self._set_available_process_id(TDE_Screen.SCREEN_ID)

        # Stage 2: Create the screen process instance
        try:
            screen_process = TDE_Screen(process_id=process_id)
        except Exception as e:
            raise RuntimeError(
                f"Error while creating screen process '{TDE_Screen.__class__.__name__}': {e}"
            ) from e

        # Stage 3: Add the screen process to the process dictionary
        try:
            self._add_process_to_dict(screen_process, process_id)
        except RuntimeError as e:
            raise RuntimeError(
                f"Failed to add process {process_id} for screen {TDE_Screen.SCREEN_ID}. "
                "This might be due to a duplicate process ID."
            ) from e

        # Stage 4: Create the screen context dictionary
        screen_context: ProcessContext = {
            "process_type": ProcessType.SCREEN,
            "process_id": process_id,
            "process_uid": screen_process.uid,
            "services": self.services_manager,
        }

        # Stage 5: Get screen class definition from process instance
        try:
            tde_screen = screen_process.get_screen()
        except Exception as e:
            raise RuntimeError(
                f"Failed to get screen class from process {process_id} for screen {TDE_Screen.SCREEN_ID}."
            ) from e

        # Stage 6: Create the screen instance
        try:
            screen_instance = tde_screen(screen_context)
        except Exception as e:
            raise RuntimeError(f"Failed to create screen instance for {TDE_Screen.SCREEN_ID}: {e}") from e

        # Stage 7: Store the screen instance in the dictionary
        self._screen_instance_dict[process_id] = screen_instance

        # Stage 8: Call the pushing callback with the new screen instance
        try:
            await self._pushing_callback(screen_instance)
        except Exception as e:
            raise RuntimeError(
                f"Error while executing callback '{self._pushing_callback}' "
                f"for screen '{TDE_Screen.__class__.__name__}': {e}"
            ) from e
