from .token import Token
from .token_type import TokenType
from .asts.expr import Expr, Binary, Unary, Literal, Grouping
from .lox import Lox
from .error import LoxParseError

class Parser:
    """
    Parser class for th Lox language. The following grammar is encoded:
    expression  => equality
    equality    => comparison ( ( "!=" | "==" ) comparison )*
    comparison  => term ( ( ">" | ">=" | "<" | "<=" ) term )*
    term        => factor ( ( "-" | "+" ) factor )*
    factor      => unary ( ( "/" | "*" ) unary )*
    unary       => ( "!" | "-" ) unary | primary
    primary     => NUMBER | STRING | "true" | "false" | "nil" | "(" expression ")"
    """

    def __init__(self, tokens: list[Token]):
        self.tokens: list[Token] = tokens
        self.current = 0

    def parse(self) -> Expr | None:
        try: 
            return self.expression()
        except LoxParseError:
            return None

    ########### Grammar rules encoding

    def expression(self) -> Expr:
        """expression  => equality"""
        return self.equality()
    
    def equality(self) -> Expr:
        """equality    => comparison ( ( "!=" | "==" ) comparison )*"""
        expr: Expr = self.comparison()

        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator: Token = self.previous()
            right: Expr = self.comparison()
            expr = Binary(expr, operator, right)

        return expr
    
    def comparison(self) -> Expr:
        """comparison  => term ( ( ">" | ">=" | "<" | "<=" ) term )*"""
        expr: Expr = self.term()

        while self.match(TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL):
            operator: Token = self.previous()
            right: Expr = self.term()
            expr = Binary(expr, operator, right)

        return expr

    def term(self) -> Expr: 
        """term        => factor ( ( "-" | "+" ) factor )*"""
        expr: Expr = self.factor()

        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator: Token = self.previous()
            right: Expr = self.term()
            expr = Binary(expr, operator, right)

        return expr

    def factor(self) -> Expr:
        """factor      => unary ( ( "/" | "*" ) unary )*"""
        expr: Expr = self.unary()

        while self.match(TokenType.STAR, TokenType.SLASH):
            operator: Token = self.previous()
            right: Expr = self.term()
            expr = Binary(expr, operator, right)

        return expr

    def unary(self) -> Expr:
        """unary       => ( "!" | "-" ) unary | primary"""

        if self.match(TokenType.BANG, TokenType.MINUS):
            operator: Token = self.previous()
            right: Expr = self.unary()
            return Unary(operator, right)
        return self.primary()
    
    def primary(self) -> Expr:
        """primary     => NUMBER | STRING | "true" | "false" | "nil" | "(" expression ")\""""
        if self.match(TokenType.FALSE): return Literal(False)
        if self.match(TokenType.TRUE): return Literal(True)
        if self.match(TokenType.NIL): return Literal(None)
        if self.match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self.previous().literal)
        if self.match(TokenType.LEFT_PAREN):
            expr: Expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression")
            return Grouping(expr)
        raise self.error(self.peek(), "Expect expression")

    
    ############ Helper methods for traversing the tokens

    def match(self, *token_types: TokenType) -> bool:
        """
        Similar to check(), but with multiple token types.
        Also consumes the token if a match is found.
        """
        for token_type in token_types:
            if self.check(token_type):
                self.advance()
                return True
        return False
    
    def consume(self, token_type: TokenType, message: str) -> Token:
        """
        Consume the next token and make sure it matches the requested token.
        Otherwise throw an error.
        """
        if self.check(token_type): return self.advance()
        raise self.error(self.peek(), message)
    
    def check(self, token_type: TokenType) -> bool:
        """Check if the next token is of the selected type"""
        if self.isAtEnd():
            return False
        return self.peek().token_type == token_type
    
    def peek(self) -> Token:
        """Get next token"""
        return self.tokens[self.current]
    
    def advance(self) -> Token:
        """Advances the token pointer if not at the end of the stream"""
        if not self.isAtEnd(): self.current +=1
        return self.previous()
    
    def previous(self) -> Token:
        """Get previously seen token for looking back"""
        return self.tokens[self.current-1]
    
    def isAtEnd(self) -> bool:
        """Check if the token stream is at the end"""
        return self.peek().token_type == TokenType.EOF
    
    def error(self, token: Token, message: str) -> LoxParseError:
        Lox.error(token, message)
        return LoxParseError()
    
    def synchronise(self):
        """
        Sync method used to sync up the parser after an error.
        Syncing is assumed after a semicolon (;) or on keywords
        """
        # advance to token directly after error
        self.advance()
        while not self.isAtEnd():
            # If a semicolon is found, sync directly after
            if self.previous().token_type == TokenType.SEMICOLON: return
            # On keywords, sync up
            match self.peek().token_type:
                case TokenType.CLASS | TokenType.FUN | TokenType.VAR   | TokenType.RETURN \
                    | TokenType.FOR  | TokenType.IF  | TokenType.WHILE | TokenType.PRINT:
                    return
                
            # No match, discard token and keep searching
            self.advance()
