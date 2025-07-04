"servicetemplate.py - Template for services. Replace this with description."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from term_desktop.services.manager import ServicesManager

# Textual imports
# from textual import log   #? <- use this for logging to Textual dev console
from term_desktop.services.servicebase import TDEServiceBase

# Textual library imports

# Local imports


class ShellService(TDEServiceBase):

    #####################
    # ~ Initialzation ~ #
    #####################

    SERVICE_ID = "shell_service"

    def __init__(
        self,
        services_manager: ServicesManager,
    ) -> None:
        """
        Initialize the Shell service.
        """
        super().__init__(services_manager)
        self.validate()

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
        self.log("Starting Shell service")
        """Start the Shell service. service."""

        return True

    async def stop(self) -> bool:
        self.log("Stopping Shell service")
        return True

    ################
    # ~ Internal ~ #
    ################
    # This section is for methods that are only used internally
    # These should be marked with a leading underscore.
