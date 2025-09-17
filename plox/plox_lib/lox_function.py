from typing import TYPE_CHECKING

from .lox_callable import LoxCallable
from .asts.stmt import Function
from .environment import Environment

from . import control_flow
from . import lox_instance

if TYPE_CHECKING:
    from .interpreter import Interpreter

class LoxFunction(LoxCallable):
    """
    Class representing a Lox Function or Method.
    """

    def __init__(self, declaration: Function, closure: Environment, isInitializer: bool = False):
        self.closure: Environment = closure
        self.declaration: Function = declaration
        self.isInitializer: bool = isInitializer
        
    def call(self, interpreter: "Interpreter", arguments: list[object]) -> object:
        """Execute the function body with the provided arguments. the 'visitCallExpr' method should do checking on correct parameter type and arity."""
        # Create a new environment with the current environment in the interpreter as a parent (modeled similar to a stack)
        environment: Environment = Environment(self.closure)
        for i in range(len(self.declaration.params)):
            environment.define(self.declaration.params[i].lexeme, arguments[i])

        # Since the call stack can become quite deep and complex when a function is called
        # the easiest method is to handle return as if it is an exception. This way control flow can be interrupted
        # and handled neatly in the interpreter internals through standard exception handling.
        try:
            interpreter.executeBlock(self.declaration.body, environment)
        except control_flow.Return as r:
            if self.isInitializer:
                return self.closure.getAt("this", 0)
            return r.value
        
        # Initializer methods automatically return a reference to the class instance
        if self.isInitializer:
            return self.closure.getAt("this", 0)
        return None
        
    def bind(self, instance: "lox_instance.LoxInstance") -> "LoxFunction":
        environment: Environment = Environment(self.closure)
        environment.define("this", instance)
        return LoxFunction(self.declaration, environment, self.isInitializer)
    
    def arity(self) -> int:
        return len(self.declaration.params)
    
    def __str__(self) -> str:
        return f"<fn {self.declaration.name.lexeme} >"
    
    def __repr__(self) -> str:
        return self.__str__()