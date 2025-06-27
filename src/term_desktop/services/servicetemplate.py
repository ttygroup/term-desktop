"servicetemplate.py - Template for services. Replace this with description."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager

# Textual imports
# from textual import log   #? <- use this for logging to Textual dev console
from term_desktop.services.servicebase import BaseService

# Textual library imports

# Local imports


class ServiceTemplate(BaseService):

    def __init__(
        self, 
        services_manager: ServicesManager, 
    ) -> None:
        """        
        Initialize the [INSERT SERVICE NAME HERE]
        """
        super().__init__(services_manager)

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
