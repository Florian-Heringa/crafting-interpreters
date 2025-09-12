from typing import TYPE_CHECKING

from .lox_callable import LoxCallable
from .asts.stmt import Function
from .environment import Environment

from . import control_flow

if TYPE_CHECKING:
    from .interpreter import Interpreter

class LoxFunction(LoxCallable):

    def __init__(self, declaration: Function, closure: Environment):
        self.closure: Environment = closure
        self.declaration: Function = declaration
        
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
            return r.value
        
        return None
        
        
    
    def arity(self) -> int:
        return len(self.declaration.params)
    
    def __str__(self) -> str:
        return f"<fn {self.declaration.name.lexeme} >"