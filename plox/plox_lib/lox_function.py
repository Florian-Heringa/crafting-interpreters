from typing import TYPE_CHECKING

from .lox_callable import LoxCallable
from .asts.stmt import Function
from .environment import Environment

if TYPE_CHECKING:
    from .interpreter import Interpreter

class LoxFunction(LoxCallable):

    def __init__(self, declaration: Function):
        self.declaration = declaration

    def call(self, interpreter: "Interpreter", arguments: list[object]) -> object:
        environment: Environment = Environment(interpreter.globals)
        for i in range(len(self.declaration.params)):
            environment.define(self.declaration.params[i].lexeme, arguments[i])

        interpreter.executeBlock(self.declaration.body, environment)
        return None
    
    def arity(self) -> int:
        return len(self.declaration.params)
    
    def __str__(self) -> str:
        return f"<fn {self.declaration.name.lexeme} >"