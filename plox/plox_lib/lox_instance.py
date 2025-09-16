from .token import Token
from .error import LoxRuntimeError

from . import lox_class
from . import lox_function

class LoxInstance:
    """
    A container for a Lox Class instance. Holds values in 'self.fields'. For methods, refers back to the original LoxClass.
    """

    def __init__(self, lox_class: "lox_class.LoxClass"):
        self.lox_class: "lox_class.LoxClass" = lox_class
        self.fields: dict[str, object] = {} 

    def __str__(self) -> str:
        return f"<{self.lox_class.name} instance>"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def get(self, name: Token) -> object:
        """
        This method returns a property; 
        either the value of a field, or a method on the class, with 'this' bound.
        """
        if name.lexeme in self.fields:
            return self.fields.get(name.lexeme)
        
        method: "lox_function.LoxFunction | None" = self.lox_class.find_method(name.lexeme)
        if method is not None:
            return method.bind(self)
        
        raise LoxRuntimeError(name, f"Undefined property '{name.lexeme}'.")
    
    def set(self, name: Token, value: object):
        self.fields[name.lexeme] = value