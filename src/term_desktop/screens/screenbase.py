from __future__ import annotations
from abc import ABC, abstractmethod
# from typing import TYPE_CHECKING #, Any, Callable
# if TYPE_CHECKING:
    # from term_desktop.services.servicesmanager import ServicesManager
    # from textual.worker import Worker  

# from textual import log

# class CustomWindowMounts(TypedDict, total=False):
#     """A dictionary of custom mounts to be added to the window.
#     You can attach one widget to each of the following keys."""

#     above_topbar: type[Widget]  #      mounted above the top bar.
#     below_topbar: type[Widget]  #      mounted below the top bar
#     left_pane: type[Widget]  #         mounted to the left of the content area
#     right_pane: type[Widget]  #        mounted to the right of the content area
#     above_bottombar: type[Widget]  #   mounted above the bottom bar
#     below_bottombar: type[Widget]  #   mounted below the bottom bar


class TDEScreen(ABC):


    def __init__(self, id: str) -> None:
        """
        The ID is set by the screen service when it initializes the screen process.
        """
        self.id = id

    @abstractmethod
    def build(self) -> Screen:
        """
        
        """
        pass


    # @classmethod
    # def validate(cls) -> None:

    #     required_members = {
    #         "APP_NAME": "class attribute",
    #         "APP_ID": "class attribute",
    #         # more will go here as needed
    #     }

    #     for attr_name, kind in required_members.items():

    #         try:
    #             attr = getattr(cls, attr_name)
    #         except AttributeError:
    #             raise NotImplementedError(f"{cls.__name__} must implement {attr_name} ({kind}).")
    #         else:
    #             if attr is None:
    #                 raise NotImplementedError(f"{cls.__name__} must implement {attr_name} ({kind}).")

    #     missing = cls.__abstractmethods__
    #     if missing:
    #         cls.BROKEN = True
    #         cls.MISSING_METHODS = missing
    #         raise NotImplementedError(
    #             f"{cls.__name__} is missing the following abstract methods: \n"
    #             f"{', '.join(missing)}\n"
    #             "Please implement them to make the screen functional."
    #         )