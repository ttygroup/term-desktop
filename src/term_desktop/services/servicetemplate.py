"servicetemplate.py - Template for services. Replace this with description."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager

# Textual imports
from term_desktop.services.servicebase import TDEServiceBase
from term_desktop.aceofbase import AceOfBase  # , ProcessType

# Textual library imports

# Local imports


class DummyServiceProcessBase(AceOfBase):
    """
    This would be whatever type of process the service is controlling.
    TDEAppBase for apps, TDEWindowBase for windows, etc.
    """


class ServiceTemplate(TDEServiceBase[DummyServiceProcessBase]):

    #####################
    # ~ Initialzation ~ #
    #####################

    SERVICE_ID = "foo_service"

    def __init__(self, services_manager: ServicesManager) -> None:
        """
        Initialize the [INSERT SERVICE NAME HERE]
        """
        super().__init__(services_manager)

    ################
    # ~ Messages ~ #
    ################
    # None yet

    ####################
    # ~ External API ~ #
    ####################
    # Methods that might need to be accessed by
    # anything else in TDE, including other services.

    async def start(self) -> bool:
        """Start the [INSERT SERVICE NAME HERE] service."""
        self.log("Starting Foo service")

        if True:
            return True
        else:
            return False

    async def stop(self) -> bool:
        self.log("Stopping Window service")
        if True:
            return True
        else:
            return False

    ################
    # ~ Internal ~ #
    ################
    # Methods that are only used inside this service.
    # These should be marked with a leading underscore.
