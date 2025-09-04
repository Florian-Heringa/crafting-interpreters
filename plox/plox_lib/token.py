from pydantic.dataclasses import dataclass
from typing import Any

from .token_type import TokenType

@dataclass
class Token:

    token_type: TokenType
    lexeme: str
    literal: str | float | None
    line: int

    def __str__(self):
        return f"[Line {self.line}] {self.token_type} => {self.lexeme}, {self.literal}"