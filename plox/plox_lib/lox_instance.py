from . import lox_class

class LoxInstance:

    def __init__(self, newClass: "lox_class.LoxClass"):
        self.lox_class: "lox_class.LoxClass" = newClass

    def __str__(self) -> str:
        return f"<{self.lox_class.name} instance>"