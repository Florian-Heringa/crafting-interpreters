from plox_lib import Interpreter, Scanner, Token, Parser

def test_simple_expression():

    source = "2+2"

    scanner = Scanner(source)
    tokens: list[Token] = scanner.scanTokens()
    parser = Parser(tokens)
    expression = parser.parse()
    assert expression is not None
    interpreter = Interpreter()
    assert interpreter.interpret(expression) == 4