"""Base class for all games. \n"""

# from abc import ABC, abstractmethod
from __future__ import annotations
from dataclasses import dataclass

from textual.message import Message
from textual.widget import Widget

from textual_games.enums import TableType


class GameBase(Widget):

    def validate_interface(game: GameBase):
        """Validates if a game class implements the required contract."""

        required_members = {
            "game_name": "attribute",
            "calculate_winner": "method",
            "start_game": "method",
            "get_possible_moves": "method",
            "execute_move": "method",
            "clear_focus": "method",
            "clear_table": "method",
            "render_function": "method",
        }
            
        for member, kind in required_members.items():
            try:
                getattr(game, member)
            except AttributeError:
                raise NotImplementedError(f"{game.__name__} must implement {member} ({kind}).")

    class StartGame(Message):
        """Posted when a game is either mounted or restarted. \n
        Handled by start_game in TextualGames class."""

        def __init__(
                self,
                game: GameBase,
                players: int,
                table_type: TableType,
                rows: int | None = None,
                columns: int | None = None,
                max_depth: int | None = None
            ):
            super().__init__()
            self.game = game
            self.players = players
            self.rows = rows
            self.columns = columns
            self.table_type = table_type
            self.max_depth = max_depth


class GameState:

    def __init__(self, state_obj: object):
        #! This is currently generic, but it should use some kind of structured system.

        self.state_obj = state_obj        # starting with integer board.