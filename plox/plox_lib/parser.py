from .token import Token
from .token_type import TokenType
from .asts.stmt import *
from .asts.expr import *
from .error import LoxParseError
from .params import Params

from . import lox

class Parser:
    """
    Parser class for the Lox language. The following grammar is encoded:
    program     => declaration* EOF
    declaration => classDecl | funDecl | varDecl | statement
    classDecl   => "class" IDENTIFIER ( "<" IDENTIFIER )? "{" function* "}"
    funDecl     => "fun" function
    function    => IDENTIFIER "(" parameters? ")" block
    parameters  => IDENTIFIER ( "," IDENTIFIER )*
    varDecl     => "var" IDENTIFIER ( "=" expression )? ";"
    statement   => exprStmt | forStmt | ifStmt | printStmt | returnStmt | whileStmt | block
    exprStmt    => expression ";"
    forStmt     => "for" "(" ( varDecl | exprStmt | ";") expression? ";" expression? ";" ")" statement
    ifStmt      => "if" "(" expression ")" statement ( "else" statement )?
    printStmt   => "print" expression ";" 
    returnStmt  => "return" expression ";"
    whileStmt   => "while" "(" expression ")" statement
    block       => "{" declaration* "}"
    expression  => assignment
    assignment  => ( call "." )? IDENTIFIER "=" assignment | logic_or
    logic_or    => logic_and ("or" logic_and)*
    logic_and   => equality ("and" equality)*
    equality    => comparison ( ( "!=" | "==" ) comparison )*
    comparison  => term ( ( ">" | ">=" | "<" | "<=" ) term )*
    term        => factor ( ( "-" | "+" ) factor )*
    factor      => unary ( ( "/" | "*" ) unary )*
    unary       => ( "!" | "-" ) unary | call
    call        => primary ( "(" arguments? ")" | "." IDENTIFIER )*
    arguments   => expression ( "," expression )*
    primary     => NUMBER | STRING | "true" | "false" | "nil" | "(" expression ")" | IDENTIFIER | "super" "." IDENTIFIER
    """

    def __init__(self, tokens: list[Token]):
        self.tokens: list[Token] = tokens
        self.current = 0

    def parse(self) -> list[Stmt]:
        """program     => declaration* EOF"""
        statements: list[Stmt] = []
        while not self.isAtEnd():
            try:
                statements.append(self.declaration())
            except LoxParseError as e:
                self.synchronise()
        
        return statements

    ########### Grammar rules encoding
    
    def declaration(self) -> Stmt:
        """declaration => classDecl | funDecl | varDecl | statement"""
        if self.match(TokenType.CLASS):
            return self.classDeclaration()
        if self.match(TokenType.FUN):
            return self.function("function")
        if self.match(TokenType.VAR):
            return self.varDeclaration()
        return self.statement()
    
    def classDeclaration(self) -> Stmt:
        """classDecl   => "class" IDENTIFIER ( "<" IDENTIFIER )? "{" function* "}\""""
        name: Token = self.consume(TokenType.IDENTIFIER, "Expect class name.")

        superclass: Variable | None = None
        if self.match(TokenType.LESS):
            superclass = Variable(self.consume(TokenType.IDENTIFIER, "Expect"))

        self.consume(TokenType.LEFT_BRACE, "Expect '{' before class body")
        methods: list[Function] = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.isAtEnd():
            methods.append(self.function("method"))
        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after class body.")

        return Class(name, superclass, methods)
    
    def function(self, kind: str) -> Function:
        """function    => IDENTIFIER "(" parameters? ")" block"""
        name: Token = self.consume(TokenType.IDENTIFIER, f"Expect {kind} name.")
        self.consume(TokenType.LEFT_PAREN, f"Expect'(' after {kind} name.")
        parameters: list[Token] = []

        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                if len(parameters) > Params.MAX_ARGUMENT_COUNT:
                    self.error(self.peek(), f"Can't have more than {Params.MAX_ARGUMENT_COUNT} parameters.")
                parameters.append(self.consume(TokenType.IDENTIFIER, "Expect parameter name."))
                if not self.match(TokenType.COMMA):
                    break
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")
        self.consume(TokenType.LEFT_BRACE, f"Expect '{{' before {kind} body.")
        body: list[Stmt] = self.block()
        return Function(name, parameters, body)
        
    def varDeclaration(self) -> Stmt:
        """varDecl     => "var" IDENTIFIER ( "=" expression )? ";\""""
        name: Token = self.consume(TokenType.IDENTIFIER, "Expect variable name")
        initializer: Expr | None = None
        if (self.match(TokenType.EQUAL)):
            initializer = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration")
        return Var(name, initializer)

    def statement(self) -> Stmt:
        """statement   => exprStmt | forStmt | ifStmt | printStmt | whileStmt | block"""
        if self.match(TokenType.IF):
            return self.ifStatement()
        if self.match(TokenType.PRINT):
            return self.printStatement()
        if self.match(TokenType.LEFT_BRACE):
            return Block(self.block())
        if self.match(TokenType.RETURN):
            return self.returnStatement()
        if self.match(TokenType.WHILE):
            return self.whileStatement()
        if self.match(TokenType.FOR):
            return self.forStatement()
        return self.expressionStatement()
    
    def forStatement(self) -> Stmt:
        """
        forStmt     => "for" "(" ( varDecl | exprStmt | ";") expression? ";" expression? ";" ")" statement
        Syntactic sugar for variable declaration and while loop
        """
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")

        initializer: Stmt | None = None
        if (self.match(TokenType.SEMICOLON)):
            initializer = None
        elif self.match(TokenType.VAR):
            initializer = self.varDeclaration()
        else:
            initializer = self.expressionStatement()

        condition: Expr | None = None
        if (not self.check(TokenType.SEMICOLON)):
            condition = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        increment: Expr | None = None
        if (not self.check(TokenType.RIGHT_PAREN)):
            increment = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")

        body: Stmt = self.statement()

        # Wrap the entire for loop into a block
        # {
        #   Initializer
        #   while (condition) { body; increment; }
        # }
        if increment is not None:
            body = Block([body, Expression(increment)])

        if condition is None:
            condition = Literal(True)
        
        body = While(condition, body)

        if initializer is not None:
            body = Block([initializer, body])

        return body        
    
    def printStatement(self) -> Stmt:
        """printStmt   => "print" expression ";" """
        value: Expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value")
        return Print(value)
    
    def returnStatement(self) -> Stmt:
        keyword: Token = self.previous()
        value: Expr | None = None
        if not self.check(TokenType.SEMICOLON):
            value  = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after return value.")
        return Return(keyword, value)
    
    def ifStatement(self) -> Stmt:
        """ifStmt      => "if" "(" expression ")" statement ( "else" statement )?"""
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition: Expr = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition")
        thenBranch: Stmt = self.statement()
        
        return If(condition, thenBranch, self.statement() if self.match(TokenType.ELSE) else None)
    
    def whileStatement(self) -> Stmt:
        """whileStmt   => "while" "(" expression ")" statement"""
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition: Expr = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after while condition.")
        body: Stmt = self.statement()

        return While(condition, body)

    def expressionStatement(self) -> Stmt:
        """exprStmt    => expression ";\""""
        expr: Expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression")
        return Expression(expr)
    
    def block(self) -> list[Stmt]:
        """block       => "{" declaration* "}\""""
        statements: list[Stmt] = []

        while not self.check(TokenType.RIGHT_BRACE) and not self.isAtEnd():
            statements.append(self.declaration())

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")

        return statements
    
    def expression(self) -> Expr:
        """expression  => assignment"""
        return self.assignment()
    
    def assignment(self) -> Expr:
        """assignment  => ( call "." )? IDENTIFIER "=" assignment | logic_or"""

        # Start parsing the expression
        expr: Expr = self.logic_or()

        # if the found expression is followed by an "=", it *must* be an assignment
        # So it should fall through to the 'primary' rule, yielding a Variable.
        # Anything else results in an error
        if self.match(TokenType.EQUAL):
            # The info of "=" itself
            equals: Token = self.previous()
            # the rhs, which can be an equality itself, otherwise drop down the priority list
            value: Expr = self.assignment()

            # If what we found for the lhs is a variable, parse the rhs and assign
            if isinstance(expr, Variable):
                name: Token = expr.name
                return Assign(name, value)
            # If the lhs has the form of a 'Get' expression, transform it into
            # a corresponding 'Set' expression
            elif isinstance(expr, Get):
                return Set(expr.object, expr.name, value)
            self.error(equals, "Invalid assignment target.")
        
        return expr
    
    def logic_or(self) -> Expr:
        expr: Expr = self.logic_and()

        if self.match(TokenType.OR):
            operator: Token = self.previous()
            right: Expr = self.logic_and()
            return Logical(expr, operator, right)

        return expr

    def logic_and(self)-> Expr:
        expr: Expr = self.equality()

        if self.match(TokenType.AND):
            operator: Token = self.previous()
            right: Expr = self.equality()
            return Logical(expr, operator, right)

        return expr
    
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
        return self.call()
    
    
    def call(self) -> Expr:
        """call        => primary ( "(" arguments? ")" | "." IDENTIFIER )*"""
        expr: Expr = self.primary()

        while True:
            if self.match(TokenType.LEFT_PAREN):
                expr = self.finishCall(expr)
            elif self.match(TokenType.DOT):
                name: Token = self.consume(TokenType.IDENTIFIER, "Expect property name after '.'.")
                expr = Get(expr, name)
            else:
                break

        return expr        

    def finishCall(self, callee: Expr) -> Expr:
        arguments: list[Expr] = []

        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                if len(arguments) > Params.MAX_ARGUMENT_COUNT:
                    self.error(self.peek(), f"Can't have more than {Params.MAX_ARGUMENT_COUNT} arguments.")
                arguments.append(self.expression())
                if not self.match(TokenType.COMMA):
                    break

        paren: Token = self.consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments")

        return Call(callee, paren, arguments)

    def primary(self) -> Expr:
        """primary     => NUMBER | STRING | "true" | "false" | "nil" | "(" expression ")" | IDENTIFIER | "super" "." IDENTIFIER"""
        if self.match(TokenType.FALSE): return Literal(False)
        if self.match(TokenType.TRUE): return Literal(True)
        if self.match(TokenType.NIL): return Literal(None)
        if self.match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self.previous().literal)
        if self.match(TokenType.SUPER):
            keyword: Token = self.previous()
            self.consume(TokenType.DOT, "Expect '.' after 'super'.")
            method: Token = self.consume(TokenType.IDENTIFIER, "Expect superclass method name.")
            return Super(keyword, method)
        if self.match(TokenType.THIS):
            return This(self.previous())
        if self.match(TokenType.IDENTIFIER):
            return Variable(self.previous())
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
        lox.Lox.error(token, message)
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
