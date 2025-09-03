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
        Initialize the file association service.
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

    def get_associated_application(self, file_extension: str) -> str | None:
        """
        Get the application associated with a given file extension.

        Args:
            file_extension (str): The file extension to look up (e.g., '.txt').

        Returns:
            str | None: The associated application ID, or None if not found.
        """
        # Placeholder implementation

    ################
    # ~ Internal ~ #
    ################
    # These should be marked with a leading underscore.
