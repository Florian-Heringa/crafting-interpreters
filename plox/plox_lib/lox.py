from os import PathLike

from .token import Token
from . token_type import TokenType

class Lox:

    hadError = False

    def __init__(self):
        self.hadError = False

    def runPrompt(self):
        print("Running Prompt")

        while True:
            try:
                line = input("> ")
                self.run(line)
            except EOFError:
                print("\tExiting interactive session...")
                break
            except KeyboardInterrupt:
                print("\n\tInteractive session interrupted...", end="")
                break
            # Reset error flag
            self.hadError = False

    def runFile(self, file: PathLike):
        print(f"Running file {file}")

        with open(file, 'r') as source:
            self.run("".join(source.readlines()))
        if self.hadError:
            exit(65)
        

    def run(self, source: str):
        
        for token in source.split():
            print(token)

    @staticmethod
    def error(token: Token, message: str):
        if token.token_type == TokenType.EOF:
            Lox.report(token.line, " at end", message)
        else:
            Lox.report(token.line, f" at '{token.lexeme}'", message)

    @classmethod
    def report(cls, line: int, where: str, message: str):
        print(f"[line {line}] Error {where}: {message}")
        cls.hadError = True