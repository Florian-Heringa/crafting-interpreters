from typing import Annotated
from pydantic import constr
import re
from enum import Enum

from .token_type import TokenType

Char = Annotated[str, constr(min_length=1, max_length=1)]

def is_alpha(c: Char) -> bool:
    return bool(re.match(r"[a-zA-Z_]", c))

def is_num(c: Char) -> bool:
    return bool(re.match(r"[0-9]", c))

def is_alnum(c: Char) -> bool:
    return is_alpha(c) or is_num(c)

TOKEN_MAP = {
    "(": TokenType.LEFT_PAREN,
    ")": TokenType.RIGHT_PAREN,
    "{": TokenType.LEFT_BRACE,
    "}": TokenType.RIGHT_BRACE,
    ",": TokenType.COMMA,
    ".": TokenType.DOT,
    "-": TokenType.MINUS,
    "+": TokenType.PLUS,
    ";": TokenType.SEMICOLON,
    "*": TokenType.STAR,
    "!": TokenType.BANG,
    "=": TokenType.EQUAL,
    "<": TokenType.LESS,
    ">": TokenType.GREATER,
    "/": TokenType.SLASH
}

KEYWORDS = {
    "and": TokenType.AND,
    "class": TokenType.CLASS,
    "else": TokenType.ELSE,
    "false": TokenType.FALSE,
    "for": TokenType.FOR,
    "fun": TokenType.FUN,
    "if": TokenType.IF,
    "nil": TokenType.NIL,
    "or": TokenType.OR,
    "print": TokenType.PRINT,
    "return": TokenType.RETURN,
    "super": TokenType.SUPER,
    "this": TokenType.THIS,
    "true": TokenType.TRUE,
    "var": TokenType.VAR,
    "while": TokenType.WHILE,
}

FunctionType = Enum("FunctionType", "NONE, FUNCTION")