"fileassociations.py"

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager

# Textual imports
from term_desktop.services.servicebase import TDEServiceBase
from term_desktop.aceofbase import AceOfBase

# Textual library imports

# Local imports


class DummyServiceProcessBase(AceOfBase):
    """
    This would be whatever type of process the service is controlling.
    TDEAppBase for apps, TDEWindowBase for windows, etc.
    """


class FileAssociationService(TDEServiceBase[DummyServiceProcessBase]):

    ################
    # ~ Messages ~ #
    ################
    # None yet

    #####################
    # ~ Initialzation ~ #
    #####################

    SERVICE_ID = "file_association_service"

    def __init__(
        self,
        services_manager: ServicesManager,
    ) -> None:
        """
        Initialize the [INSERT SERVICE NAME HERE]
        """
        super().__init__(services_manager)

    ################
    # ~ Contract ~ #
    ################

    async def start(self) -> bool:
        if True:
            return True
        else:
            return False

    async def stop(self) -> bool:
        if True:
            return True
        else:
            return False

    ####################
    # ~ External API ~ #
    ####################
    # Methods that might need to be accessed by
    # anything else in TDE, including other services.

    ################
    # ~ Internal ~ #
    ################
    # These should be marked with a leading underscore.
