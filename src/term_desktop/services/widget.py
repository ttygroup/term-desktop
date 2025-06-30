from textual.widget import Widget
from term_desktop.services.manager import ServicesManager


class ServicesWidget(Widget):
    """A widget that houses the ServicesManager for mounting into the main app as
    well as querying anywhere else in the TDE."""

    def __init__(self) -> None:
        super().__init__()
        self.display = False

    def create_services_manager(self) -> None:
        """Initializes the ServicesManager instance inside this widget."""

        self._services = ServicesManager()

    async def start_services(self) -> None:
        """Starts all services managed by the ServicesManager."""

        await self._services.start_all_services()

    @property
    def services(self) -> ServicesManager:
        """Returns the ServicesManager instance."""
        return self._services
