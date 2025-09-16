from .lox_callable import LoxCallable

from . import lox_instance
from . import interpreter

class LoxClass(LoxCallable):

    def __init__(self, name):
        self.name = name

    def __str__(self) -> str:
        return self.name
    
    def call(self, interpreter: "interpreter.Interpreter", arguments: list[object]) -> object:
        instance: lox_instance.LoxInstance = lox_instance.LoxInstance(self)
        return instance
    
    def arity(self) -> int:
        return 0