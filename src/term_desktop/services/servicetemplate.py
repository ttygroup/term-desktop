"servicetemplate.py - Template for services. Replace this with description."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from term_desktop.services.manager import ServicesManager

# Textual imports
from term_desktop.services.servicebase import TDEServiceBase

# Textual library imports

# Local imports


class ServiceTemplate(TDEServiceBase):

    #####################
    # ~ Initialzation ~ #
    #####################

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
    # This section is for methods or properties that might need to be
    # accessed by anything else in TDE, including other services.

    async def start(self) -> bool:
        """Start the [INSERT SERVICE NAME HERE] service."""

        # Example of using a worker inside of a service
        # Any extra positional and keyword arguments that not part of the
        # run_worker function will be passed to the callback function.
        # Note this is set to use thread workers by default, and so the
        # callback function should NOT be async.
        #
        # worker = self.run_worker(
        #     self._func_to_run,
        #     any_args_here,
        #     name="AppLoaderWorker",
        #     description="Discovering apps in directories",
        #     group="AppLoader",
        #     exclusive=True,
        #     keyword1 = "some_value_here",
        #     keyword2 = "another_value_here",
        # )
        # some_value = await worker.wait()

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
