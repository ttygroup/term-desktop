"term-desktop"

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.screen import Screen, ScreenResultType, ScreenResultCallbackType

    # from textual.await_complete import AwaitComplete

# Textual imports
from textual import on
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
from term_desktop.common.errors import TDEException

# from term_desktop.app_sdk.appbase import TDEApp


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
            self.log.warning(
                "Pushing a screen that is not a TDEScreen. Ensure this is intentional "
                "(Most likely for small utility screens like dialogs)."
            )

        return super().push_screen(screen, callback, wait_for_dismiss)  # type: ignore

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

    def action_log_debug_readout(self) -> None:

        self.log.debug(Rule("Debug Readout"))
        self.log.debug(self.screen_stack)
        self.log.debug(self.tree)
        self.log.debug(self.services)
        self.log.debug(Rule("End of Debug Readout"))


####################
# ~ Run function ~ #
####################


def run():
    TermDesktop().run()
