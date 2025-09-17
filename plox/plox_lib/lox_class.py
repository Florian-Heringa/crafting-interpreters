from .lox_callable import LoxCallable

from . import lox_instance
from . import interpreter
from . import lox_function

class LoxClass(LoxCallable):
    """
    Container for a Lox Class. Holds methods.
    """

    def __init__(self, name: str, superclass: "LoxClass | None", methods: "dict[str, lox_function.LoxFunction]"):
        self.name: str = name
        self.superclass: LoxClass | None = superclass
        self.methods: "dict[str, lox_function.LoxFunction]" = methods

    def __str__(self) -> str:
        return f"<Class {self.name}>"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def call(self, interpreter: "interpreter.Interpreter", arguments: list[object]) -> object:
        """
        When a class is called, create an instance and, if available, call the initializer with the provided arguments.
        """
        instance: lox_instance.LoxInstance = lox_instance.LoxInstance(self)
        initializer: "lox_function.LoxFunction | None" = self.find_method("init")
        if initializer is not None:
            # Call the init method with the provided arugments in the class call
            initializer.bind(instance).call(interpreter, arguments)
        return instance
    
    def arity(self) -> int:
        if init := self.find_method("init"):
            return init.arity()
        return 0

    
    def find_method(self, name: str) -> "lox_function.LoxFunction | None":
        if name in self.methods:
            return self.methods[name]
        if self.superclass is not None:
            return self.superclass.find_method(name)
        return