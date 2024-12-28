import asyncio
import json
import importlib
import os

from gamedig.games.base import Game
from gamedig.utils import GameDefinition


class GameDig:
    """A class for querying game servers."""

    def __init__(
        self,
        game_id: str,
        host: str,
        port: int | None = None,
        given_port: int | None = None,
    ) -> None:
        """Initialize a new GameDig instance.

        Args:
            game_id: The ID of the game to query.
            host: The hostname or IP address of the game server.
            port:
                The port of the game server. If None, it will be
                loaded from the game definition.
            given_port:
                If provided, this port will override any port
                specified in the game definition or automatically detected.
        """
        self.game_id = game_id
        self.host = host
        self.port = port
        self.given_port = given_port

        self._game = None
        self._protocol = None

    async def query(
        self, timeout: float = 5.0, max_attempts: int = 3, encoding: str = "utf8"
    ):
        """Queries the game server.

        Args:
            timeout: Timeout in seconds.
            max_attempts: Maximum number of attempts to query the server.
            encoding: Encoding to use for string values.

        Returns:
            A dictionary containing the server information or raises an exception on error.
        """

        if not self._game:
            self._load_game_definition()

        protocol_module = importlib.import_module(
            f"gamedig.protocols.{self._game.protocol}"
        )
        protocol_class = getattr(protocol_module, self._game.protocol.capitalize())
        self._protocol = protocol_class(
            self, {"timeout": timeout, "max_attempts": max_attempts, "encoding": encoding, "givenTimeout": timeout, "host": self.host, "port": self.port}
        )

        return await self._protocol.query()

    def _load_game_definition(self) -> None:
        """Loads the game definition from games.json."""
        games_json_path = os.path.join(os.path.dirname(__file__), "games.json")
        with open(games_json_path, "r") as f:
            games = json.load(f)

        game_definitions = {}
        for game_name, data in games.items():
            game_definitions[game_name.lower()] = GameDefinition(
                data["name"], data["protocol"], data["port"], data.get("options", {})
            )

        if self.game_id not in game_definitions:
            raise GameDigException(f"Game '{self.game_id}' not found.")

        game_data = game_definitions[self.game_id.lower()]

        self._game = Game(self, game_data)

        if self.port is None and self._game.port:
            self.port = self._game.port

        if self.given_port is not None:
            self.port = self.given_port

        if self.port is None:
            raise GameDigException(
                f"Game '{self.game_id}' port not defined in games.json or given_port parameter."
            )


class GameDigException(Exception):
    pass


def query(options):
    """Helper function for querying a game server.

    Args:
        options: A dictionary containing the query options. Required keys:
            - type: The game type (e.g., 'tf2', 'minecraft', 'csgo').
            - host: The server hostname or IP address.

    Returns:
        A dictionary containing the server information.
    """
    game_id = options.get("type")
    host = options.get("host")
    port = options.get("port")
    given_port = options.get("givenPort")

    if not game_id or not host:
        raise GameDigException("The 'type' and 'host' options are required.")

    game_dig = GameDig(game_id, host, port, given_port)

    # Other options are optional and can be handled here
    timeout = options.get("timeout", 5.0)
    max_attempts = options.get("max_attempts", 3)
    encoding = options.get("encoding", "utf8")

    return game_dig.query(timeout=timeout, max_attempts=max_attempts, encoding=encoding)


if __name__ == "__main__":

    async def main():
        gd = GameDig("valhiem", "192.168.1.65")
        print(await gd.query(max_attempts=1))

    asyncio.run(main())
