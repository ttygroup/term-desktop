from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager


from abc import ABC, abstractmethod


class BaseService(ABC):

    def __init__(self, services_manager: ServicesManager) -> None:
        self.services_manager = services_manager

    @abstractmethod
    async def start(self) -> bool: ...

    @abstractmethod
    async def stop(self) -> bool:
        # cleanup
        ...
