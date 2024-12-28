
from gamedig.utils import GameDefinition


class Game:
    def __init__(self, gamedig, game_data: GameDefinition):
        self.gamedig = gamedig
        self.options = game_data.options
        self.protocol = game_data.protocol
        self.name = game_data.name
        self.port = game_data.port
        self.query_port = self.options.get('queryPort')

    def __getattr__(self, item: str):
        if item in self.options:
            return self.options[item]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{item}'")
