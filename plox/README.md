# Crafting Interpreters (pLox)

A python implementation of Lox, the language used in Crafting Interpreters to teach how interpreters and compilers work.

## Running the interpreter

Currently the interpreted can be accessed by running the [main.py](./main.py) file in an environment which contains the necessary dependencies. I use poetry for dependency management. All dependencies are described in the [pyproject.toml](./pyproject.toml) file in case you want to create your own environment.

Poetry can easily install the project as a module into the environment using `poetry install`. This also enables easy use of pytest, which otherwise can be messy to handle.

Running tests is then as easy as `poetry install && poetry run pytest`.

## Tools

The repository contains a tool for generating Abstract Syntax Tree (AST) definitions. This tool can be found [here](./tool/ast.py). The AST definitions are placed in the package directory under [plox_lib/asts](./plox_lib/asts/).

Running the tool directly creates the basic AST definitions as specified in `Crafting Interpreters`.

### Resources:
- [Python Visitor Pattern](https://refactoring.guru/design-patterns/visitor/python/example)