"fileassociation.py"

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from term_desktop.services.manager import ServicesManager

# Textual imports
# from textual import log   #? <- use this for logging to Textual dev console
from term_desktop.services.servicebase import BaseService

# Textual library imports

# Local imports


class FileAssociationService(BaseService):

    #####################
    # ~ Initialzation ~ #
    #####################

    def __init__(
        self,
        services_manager: ServicesManager,
    ) -> None:
        """
        Initialize the [INSERT SERVICE NAME HERE]
        """
        super().__init__(services_manager)

    ####################
    # ~ External API ~ #
    ####################
    # This section is for methods or properties that might need to be
    # accessed by anything else in TDE, including other services.

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

    ################
    # ~ Internal ~ #
    ################
    # This section is for methods that are only used internally 
    # These should be marked with a leading underscore.