# Language parametrisation options used throughout the codebase
from pydantic.dataclasses import dataclass

@dataclass
class Params:
    MAX_ARGUMENT_COUNT: int = 255