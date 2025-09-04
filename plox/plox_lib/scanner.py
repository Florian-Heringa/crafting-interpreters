from .token import Token
from .token_type import TokenType
from .lox import Lox
from .utils import Char, is_num, is_alnum, is_alpha, TOKEN_MAP, KEYWORDS

from typing import Any

class Scanner:

    def __init__(self, source: str):

        # Data initialisation
        self.source = source
        self.tokens: list[Token] = []

        # Used in scanner state management
        self.start = 0
        self.current = 0
        self.line = 1

    def scanTokens(self) -> list[Token]:
        while not self.isAtEnd():
            self.start = self.current
            self.scanToken()

        self.tokens.append(
            Token(
                token_type=TokenType.EOF, 
                lexeme="", 
                literal=None, 
                line=self.line
            )
        )

        return self.tokens

    def scanToken(self):
        c = self.advance()
        match c:
            # Simple single character tokens
            case "(" | ")" | "{" | "}" | "," | "." | "-" | "+" | ";" | "*": self.addToken(TOKEN_MAP[c])
            # Potential double character tokens
            case "!": self.addToken(TokenType.BANG_EQUAL) if self.match("=") else self.addToken(TOKEN_MAP[c])
            case "=": self.addToken(TokenType.EQUAL_EQUAL) if self.match("=") else self.addToken(TOKEN_MAP[c])
            case "<": self.addToken(TokenType.LESS_EQUAL) if self.match("=") else self.addToken(TOKEN_MAP[c])
            case ">": self.addToken(TokenType.GREATER_EQUAL) if self.match("=") else self.addToken(TOKEN_MAP[c])
            case "/": 
                if self.match("/"):
                    # In this case, a comment has been detected, which goes until the end of the line
                    # Comments are ignored while parsing
                    while self.peek() != "\n" and not self.isAtEnd():
                        self.advance()
                else:
                    self.addToken(TOKEN_MAP[c])
            # Ignore whitespace
            case " " | "\r" | "\t": ...
            case "\n": self.line += 1
            case "\"": self.string()
            case val if is_num(val): self.number()
            case chr if is_alpha(chr): self.identifier()
            case _: Lox.error(self.line, "Unexpected character...")

    def identifier(self):
        # Consume tokens until you get to a non-alphanumeric
        while is_alnum(self.peek()): self.advance()
        # Then check if the max-munched value is a keyword, otherwise interpret as identifier
        text = self.source[self.start:self.current]
        token_type = KEYWORDS.get(text, TokenType.IDENTIFIER)
        self.addToken(token_type)

    def number(self):
        while is_num(self.peek()):
            self.advance()
        # Check if it is a decimal number and consume the dot if so
        if self.peek() == "." and is_num(self.peekNext()):
            self.advance()
        while is_num(self.peek()):
            self.advance()

        self.addTokenLiteral(TokenType.NUMBER, float(self.source[self.start:self.current]))

    def string(self):
        # keep going until the string terminates, or there are no more tokens left
        while self.peek() != "\"" and not self.isAtEnd():
            if self.peek() == "\n": 
                self.line += 1
            self.advance()
            if self.isAtEnd(): 
                Lox.error(self.line, "Unterminated String")
                return
        
        # Consume the terminating "
        self.advance()

        # Get the substring
        self.addTokenLiteral(TokenType.STRING, self.source[self.start+1:self.current-1])
            
    def match(self, expected: str) -> bool:
        # Used for matching the next character after a potential 2-character token has been detected
        # If the match succeeds, consume the token (by advancing the current pointer) and return True
        # Similar to advance, but conditional on whether the match succeeds.
        if self.isAtEnd(): return False
        if self.source[self.current] != expected: return False
        self.current += 1
        return True
    
    def peek(self) -> Char:
        # Non consuming version of advance
        # lookahead for checking next character
        if self.isAtEnd():
            return '\0'
        return self.source[self.current]
    
    def peekNext(self) -> Char:
        # two character lookahead
        if self.current + 1 > len(self.source): return "\0"
        return self.source[self.current+1]

    def isAtEnd(self):
        return self.current >= len(self.source)
    
    def advance(self) -> Char:
        self.current += 1
        return self.source[self.current-1]
    
    def addToken(self, token_type: TokenType):
        self.addTokenLiteral(token_type, None)

    def addTokenLiteral(self, token_type: TokenType, literal: Any):
        # Grab the full lexeme (trivial for single and double character lexemes)
        # But for strings, for example, this includes the quotes, while the literal value
        # excludes the quotes
        text = self.source[self.start:self.current]
        self.tokens.append(Token(
            token_type=token_type,
            lexeme=text,
            literal=literal,
            line=self.line
        ))