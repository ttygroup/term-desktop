# Textual
from textual.widgets import Static
from textual.screen import Screen




class NoSelectStatic(Static):
    """This class is used in window.py and windowbar.py to create buttons."""

    @property
    def allow_select(self) -> bool:
        return False


class DummyScreen(Screen[None]):
    # This exists to force the screen to refresh when toggling the transparency.
    # It's a bit of a hack, but it works.

    def on_mount(self) -> None:
        self.dismiss()
