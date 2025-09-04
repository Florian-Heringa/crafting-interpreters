from plox_lib import Token, TokenType
from plox_lib.asts.expr import Binary, Unary, Grouping, Literal

from plox_lib import AstPrinter

from pathlib import Path

# def test_ast_generation():

#     here = Path(__file__).resolve().parent

#     base, asts = generate_asts("Expr", [
#         "Binary - left: Expr, operator: Token, right: Expr",
#         "Grouping - left: Expr",
#         "Literal - value: str | float",
#         "Unary - operator: Token, right: Expr",
#     ], write_stubs=True)

#     assert isinstance(asts["Literal"](value=10), base)

#     Binary = asts["Binary"]
#     Literal = asts["Literal"]
    
#     simple_tree = Binary(
#         left=Literal(value=10), 
#         operator=Token(TokenType.PLUS, "+", None, 1), 
#         right=Literal(value=5))
    
#     # Type checking issues here due to generated classes...
#     assert simple_tree.left.value == 10
#     assert simple_tree.right.value == 5

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