from .token import Token
from .error import LoxRuntimeError, LoxVariableAccessError

class Environment:

    def __init__(self, enclosing: "Environment | None" = None):
        self.values: dict[str, object] = {}
        self.enclosing: Environment | None = enclosing

    def __str__(self) -> str:
        return f"{self.values} => {self.enclosing}"

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
    
    def getAt(self, name: str, depth: int) -> object:
        """Same as 'get', but a certain distance (depth) up the ineritance chain of environments."""
        return self.ancestor(depth).values.get(name)
    
    def ancestor(self, distance: int) -> "Environment":
        env: Environment = self
        # Walk up the scope chain for anumber of steps
        for i in range(distance):
            if env.enclosing is None:
                raise LoxVariableAccessError("Top level reached without finding variable <THIS IS A BUG>")
            env = env.enclosing
        return env
    
    def assign(self, name: Token, value: object):
        """
        Assign a loxValue to a specified name. The input of this function is a token so we can do proper error reporting (including line number).
        """
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return
        # Go up in scope
        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return
        raise LoxRuntimeError(name, f"Undefined variable '{name.lexeme}'.")
    
    def assignAt(self, distance: int, name: Token, value: object):
        self.ancestor(distance).values[name.lexeme] = value
