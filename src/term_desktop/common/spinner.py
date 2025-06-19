# python
from typing import TYPE_CHECKING, Any
# if TYPE_CHECKING:


# Textual
from textual.widgets import Static
from textual.timer import Timer
from rich.spinner import Spinner
from rich.console import RenderableType


class SpinnerWidget(Static):
    """A widget that displays a spinner using the rich library.
    See init for details on how to use it."""

    def __init__(
        self,
        text: RenderableType = "",
        spinner_type: str = "line",
        interval: float = 0.02,
        mount_running: bool = True,
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize the spinner widget.  
        `python -m rich.spinner` to see all options

        Args:
            text (RenderableType): The text to display alongside the spinner.
            spinner_type (str): The type of spinner to use.
            interval (float, optional): The interval in seconds to update the spinner.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        ## Selected common options:

        - aesthetic
        - arc
        - arrow
        - bouncingBall
        - bouncingBar
        - boxBounce
        - boxBounce2
        - clock
        - dots
        - dots2 through to dots12
        - earth
        - grenade
        - line
        - material
        - moon
        - noise
        - point
        - pong
        - runner
        - shark
        - simpleDots
        - simpleDotsScrolling            
        """


        super().__init__(*args, **kwargs)

        self._spinner = Spinner(spinner_type, text)
        self.interval = interval
        self.mount_running = mount_running
        self.interval_timer: Timer | None = None

    def on_mount(self) -> None:
        if self.mount_running:
            self.interval_timer = self.set_interval(self.interval, self.update_spinner)

    async def update_spinner(self) -> None:
        self.log("Updating spinner")
        self.update(self._spinner)

    def pause(self, hide: bool = False) -> None:
        """Pause the spinner."""
        if self.interval_timer:
            self.interval_timer.pause()
        if hide:
            self.display = False

    def resume(self, show: bool = True) -> None:
        """Resume the spinner."""
        if self.interval_timer:
            self.interval_timer.resume()
        else:
            self.interval_timer = self.set_interval(self.interval, self.update_spinner)
        if show:
            self.display = True            
