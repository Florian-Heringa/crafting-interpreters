from os import PathLike

from .token import Token
from .token_type import TokenType
from .asts.expr import Expr
from .asts.ast_printer import AstPrinter

from .error import LoxRuntimeError
from .utils import LoxType

from .scanner import Scanner
from .parser import Parser
from .interpreter import Interpreter

class Lox:

    hadError = False
    hadRuntimeError = False

    def __init__(self):
        self.hadError = False
        self.interpreter = Interpreter()

    def runPrompt(self):
        print("Running Prompt")

        while True:
            try:
                line = input("> ")
                result = self.run(line)
                if result is not None:
                    print(result)
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
        if self.hadRuntimeError:
            exit(70)
        
    def run(self, source: str) -> LoxType:
        
        scanner: Scanner = Scanner(source)
        tokens: list[Token] = scanner.scanTokens()
        parser: Parser = Parser(tokens)
        expression: Expr | None = parser.parse()

        if self.hadError or expression is None: 
            return

        return self.interpreter.interpret(expression)

    @staticmethod
    def error(token: Token, message: str):
        if token.token_type == TokenType.EOF:
            Lox.report(token.line, " at end", message)
        else:
            Lox.report(token.line, f" at '{token.lexeme}'", message)

    @staticmethod
    def runtimeError(err: LoxRuntimeError):
        Lox.reportRuntimeError(err.token.line, err.message)        

    @classmethod
    def report(cls, line: int, where: str, message: str):
        print(f"[line {line}] Error {where}: {message}")
        cls.hadError = True

    @classmethod
    def reportRuntimeError(cls, line: int, message: str):
        print(f"{message}\n\t[Line {line}]")
        cls.hadRuntimeError = True