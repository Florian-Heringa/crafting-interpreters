from .token import Token
from .error import LoxRuntimeError

class Environment:

    def __init__(self, enclosing: "Environment | None" = None):
        self.values: dict[str, object] = {}
        self.enclosing: Environment | None = enclosing

    def define(self, name: str, value: object):
        """ 
        The way this function works allows for redefinition of variables. 
        According to the book this choice is because it interacts poorly with the REPL.
        Because remembering all defined variables might be tough.
        If I expand the REPL feature set, I plan to include vartiable lookup and overview.
        Then maybe redefinition will be removed.
        """
        self.values[name] = value

    def  get(self, name: Token) -> object:
        """
        It is an error if a variable is undefined at the moment a value is requested.
        Using a default value is quite meaningless since the language is dynamically typed.
        """
        if name.lexeme in self.values:
            return self.values.get(name.lexeme)
        # Go up in scope
        if self.enclosing is not None:
            return self.enclosing.get(name)
        raise LoxRuntimeError(name, f"Undefined variable '{name.lexeme}'.")
    
    def assign(self, name: Token, value: object):
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return
        # Go up in scope
        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return
        raise LoxRuntimeError(name, f"Undefined variable '{name.lexeme}'.")