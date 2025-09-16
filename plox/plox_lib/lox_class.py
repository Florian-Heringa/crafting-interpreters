from .lox_callable import LoxCallable

from . import lox_instance
from . import interpreter
from . import lox_function

class LoxClass(LoxCallable):
    """
    Container for a Lox Class. Holds methods.
    """

    def __init__(self, name: str, methods: "dict[str, lox_function.LoxFunction]"):
        self.name: str = name
        self.methods: "dict[str, lox_function.LoxFunction]" = methods

    def __str__(self) -> str:
        return f"<Class {self.name}>"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def call(self, interpreter: "interpreter.Interpreter", arguments: list[object]) -> object:
        instance: lox_instance.LoxInstance = lox_instance.LoxInstance(self)
        return instance
    
    def arity(self) -> int:
        return 0
    
    def find_method(self, name: str) -> "lox_function.LoxFunction | None":
        if name in self.methods:
            return self.methods[name]
        return