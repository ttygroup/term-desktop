"term-desktop"

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING  # , cast  # , Type #, Any
if TYPE_CHECKING:
    from textual.app import ComposeResult

# Textual imports
from textual.app import App
from textual.binding import Binding
from rich.rule import Rule

#################
# Local imports #
#################
from term_desktop.services import ServicesWidget
from term_desktop.screens import MainScreen

# from term_desktop.app_sdk.appbase import TDEApp


class TermDesktop(App[None]):

    TITLE = "Term-Desktop"
    CSS_PATH = "styles.tcss"

    SCREENS = {
        "main": MainScreen,
    }

    BINDINGS = [
        Binding("f8", "log_debug_readout", "Log app debug readout to dev console", show=False),
    ]

    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        self.services = ServicesWidget()
        yield self.services
        
    async def on_mount(self) -> None:

        self.services.create_services_manager()
        await self.services.start_services()
        self.call_after_refresh(self.push_screen, "main")  # push screen after everything is ready

    def action_log_debug_readout(self) -> None:

        self.log.debug(Rule("Debug Readout"))
        self.log.debug(self.screen_stack)
        self.log.debug(self.tree)
        self.log.debug(Rule("End of Debug Readout"))

####################
# ~ Run function ~ #
####################

def run():
    TermDesktop().run()
