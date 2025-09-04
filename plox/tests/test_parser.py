from plox_lib import Token, TokenType, Parser, Scanner, AstPrinter
from plox_lib.asts.expr import Binary, Unary, Literal, Grouping

def test_simple_expression():
    source = "2 + 2"

    scanner = Scanner(source)
    tokens: list[Token] = scanner.scanTokens()
    parser = Parser(tokens)
    expression = parser.parse()

    assert expression == Binary(Literal(2), Token(TokenType.PLUS, "+", None, 1), Literal(2))


def test_print_expression():
    source = "(2 + 2) / (5 - 7) == 2"
    
    scanner = Scanner(source)
    tokens: list[Token] = scanner.scanTokens()
    parser = Parser(tokens)
    expression = parser.parse()

    assert expression is not None
    assert AstPrinter().print(expression) == "(== (/ (group (+ 2 2)) (group (- 5 7))) 2)"