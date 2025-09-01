"term-desktop"

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING, Literal, Any
import sys
import inspect
from time import time
import logging

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.screen import Screen, ScreenResultType, ScreenResultCallbackType

    # from textual.await_complete import AwaitComplete

# Textual imports
from textual import LogGroup, LogVerbosity, on # type: ignore
from textual.app import App
from textual.css.query import NoMatches

# from textual.widgets import Static
from textual.binding import Binding
from rich.rule import Rule
from textual.widget import AwaitMount, Widget


#################
# Local imports #
#################
from term_desktop.services import ServicesManager
from term_desktop.screens.screenbase import TDEScreen
from term_desktop.common.exceptions import TDEException

# from term_desktop.app_sdk.appbase import TDEApp


#################
# Logging Setup #
#################


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.INFO)

# Create console handler (optional - for both file and console output)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s', 
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Add formatter to handlers
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.critical("This is a critical message")

class TermDesktop(App[None]):

    TITLE = "Term-Desktop"
    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("f8", "log_debug_readout", "Log app debug readout to dev console", show=False),
    ]

    def compose(self) -> ComposeResult:
        self.services = ServicesManager()
        yield self.services

    def on_mount(self) -> None:

        self.services.start_all_services()
        self.log()

    @on(ServicesManager.ServicesStarted)
    def all_services_started(self) -> None:

        self.services.screen_service.register_pushing_callback(self.push_tde_screen)

        # Main app tells the screen service that its ready to push the main screen now
        self.services.screen_service.push_main_screen()

    async def push_tde_screen(self, screen: TDEScreen) -> None:
        "Used by the screen service to push a TDE screen."
        await self.push_screen(screen)

    def push_screen(  # type: ignore
        self,
        screen: Screen[ScreenResultType] | str,
        callback: ScreenResultCallbackType[ScreenResultType] | None = None,
        wait_for_dismiss: Literal[False] = False,
    ):
        """Override push_screen to add validation before delegating to base class."""

        if not isinstance(screen, TDEScreen):

            # ~ NOTE: This warning system isn't exactly a great way of handling this.
            # ~ But it'll have to do for now. We can't stop every app from pushing
            # ~ utility screens that are not TDEScreens.
            self.log.debug("Pushing a screen that is not a TDEScreen. Ensure this is intentional ")

        return super().push_screen(screen, callback, wait_for_dismiss)

    def mount(
        self,
        *widgets: Widget,
        before: int | str | Widget | None = None,
        after: int | str | Widget | None = None,
    ) -> AwaitMount:

        try:
            self.query_one(ServicesManager)
        except NoMatches:
            widget1 = next(iter(widgets), None)
            if widget1 is not None:
                if isinstance(widget1, ServicesManager):
                    return super().mount(
                        *widgets,
                        before=before,
                        after=after,
                    )
                else:
                    raise TDEException("Cannot mount widgets directly to the app. ")
            else:
                raise ValueError("No widgets provided to mount. ")
        else:
            raise TDEException("Cannot mount widgets directly to the app.")

    #! Override
    def switch_screen(self, screen: Screen | str) -> None:  # type: ignore
        raise TDEException(
            "Cannot switch screens directly in Term-Desktop. "
            "Use the screen service to push screens instead."
        )

    #! Override
    def install_screen(self, screen: Screen, name: str) -> None:  # type: ignore
        raise TDEException(
            "Cannot install screens directly in Term-Desktop. "
            "Use the screen service to push screens instead."
        )
        
    #! Override
    def _log(
        self,
        group: LogGroup,
        verbosity: LogVerbosity,
        _textual_calling_frame: inspect.Traceback,
        *objects: Any,
        **kwargs: Any,
    ) -> None:
        
        devtools = self.devtools
        if devtools is None or not devtools.is_connected:
            return

        if verbosity.value > LogVerbosity.NORMAL.value and not devtools.verbose:
            return

        try:
            from textual_dev.client import DevtoolsLog

            if len(objects) == 1 and not kwargs:
                #! modified next 3 lines
                log_msg_obj = DevtoolsLog(objects, caller=_textual_calling_frame)
                devtools.log(
                    log_msg_obj,
                    group,
                    verbosity,
                )
            else:
                output = " ".join(str(arg) for arg in objects)
                if kwargs:
                    key_values = " ".join(
                        f"{key}={value!r}" for key, value in kwargs.items()
                    )
                    output = f"{output} {key_values}" if output else key_values
                #! modified next 3 lines
                log_msg_obj = DevtoolsLog(objects, caller=_textual_calling_frame)
                devtools.log(
                    log_msg_obj,
                    group,
                    verbosity,
                )                       
        except Exception as error:
            self._handle_exception(error)
        else:
            log_payload = {
                "group": group.value,
                "verbosity": verbosity.value,
                "timestamp": int(time()),
                "path": getattr(log_msg_obj.caller, "filename", ""),
                "line_number": getattr(log_msg_obj.caller, "lineno", 0),
            }
        

    def action_log_debug_readout(self) -> None:

        self.log.debug(Rule("Debug Readout"))
        screens = "Current Screens: "
        for screen in self.screen_stack:
            if isinstance(screen, TDEScreen):
                screens += f"{screen.process_id}, "
            else:
                screens += f"{str(screen)}, "
        self.log.debug(screens)
        self.log.debug(self.services)
        self.log.debug(Rule("End of Debug Readout"))


####################
# ~ Run function ~ #
####################


def run() -> None:
    app = TermDesktop()
    app.run()
    sys.exit(app.return_code)
