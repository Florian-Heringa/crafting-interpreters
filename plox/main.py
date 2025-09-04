from argparse import ArgumentParser
from os import PathLike
from sys import exit

from plox_lib import Lox

if __name__ == "__main__":

    parser = ArgumentParser(prog="pLox", description="Interpreter for the language 'Lox' implemented in Python", epilog="- Florian Heringa 2025")
    parser.add_argument("files", nargs="*")

    args = parser.parse_args()

    lox = Lox()

    if len(args.files) == 0:
        lox.runPrompt()
    else:
        for file in args.files:
            lox.runFile(file)