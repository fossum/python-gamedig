class Base:
    def __init__(self, gamedig, timeout: float, max_attempts: int, encoding: str):
        """"""
        self.gamedig = gamedig
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.encoding = encoding

    async def query(self):
        raise NotImplementedError("Subclasses must implement this method.")