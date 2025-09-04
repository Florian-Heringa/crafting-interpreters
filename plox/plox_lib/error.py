from .token import Token

class LoxParseError(Exception):
    ...

class LoxRuntimeError(Exception):

    def __init__(self, token: Token, message: str):
        super().__init__()
        self.token = token
        self.message = message