from textual.widget import Widget


class ShellSession(AceOfBase):

    @abstractmethod
    def get_layout(self) -> ShellManager:
        """Returns the main shell layout widget to mount on screen."""

    @abstractmethod
    def session_id(self) -> str:
        """Returns a unique identifier for this shell session."""

    def on_enter(self) -> None:
        """Called when this shell session becomes active."""

    def on_exit(self) -> None:
        """Called before this session is replaced or terminated."""


class TDEShellSession:
    """
    Terminal Desktop Environment Shell Session.
    This class implements the ShellSession interface for the TDE.
    It provides methods to get the shell layout and session ID.
    """

    def get_layout(self) -> ShellManager:
        """Returns the main shell layout widget to mount on screen."""
        return ShellManager()

    def session_id(self) -> str:
        """Returns a unique identifier for this shell session."""
        return "tde_shell_session"
