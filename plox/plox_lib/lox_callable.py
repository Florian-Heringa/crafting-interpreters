# from .interpreter import Interpreter 

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .interpreter import Interpreter

class LoxCallable(ABC):
    
    @abstractmethod
    def call(self, interpreter: "Interpreter", arguments: list[object]) -> object:
        ...

    @abstractmethod
    def arity(self) -> int:
        ...