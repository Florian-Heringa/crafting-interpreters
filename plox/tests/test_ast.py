from plox_lib import Token, TokenType
from plox_lib.asts.expr import Binary, Unary, Grouping, Literal

from plox_lib import AstPrinter

from pathlib import Path

def test_ast_file_generation():

    node = Binary(Literal(10), Token(TokenType.PLUS, "+", None, 1), Literal(5))
    assert node.left.value == 10
    assert node.right.value == 5

def test_expr_print_01():

    expr = Binary(
        Unary(
            Token(TokenType.MINUS, "-", None, 1),
            Literal(123)
        ),
        Token(TokenType.STAR, "*", None, 1),
        Grouping(Literal(45.67))
    )

    printer = AstPrinter()

    assert printer.print(expr) == "(* (- 123) (group 45.67))"