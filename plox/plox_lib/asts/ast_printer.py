from typing import Any
from .expr import *

class AstPrinter(Visitor):

    def print(self, expr: Expr) -> str:
        return expr.accept(self)
    
    def visitBinaryExpr(self, expr: Binary) -> str:
        return self.parenthesize(expr.operator.lexeme, expr.left, expr.right)
    
    def visitGroupingExpr(self, expr: Grouping) -> str:
        return self.parenthesize("group", expr.expression)
    
    def visitLiteralExpr(self, expr: Literal) -> Any:
        if (expr.value == None): return "nil"
        return f"{expr.value:g}"
    
    def visitUnaryExpr(self, expr: Unary) -> Any:
        return self.parenthesize(expr.operator.lexeme, expr.right)

    def parenthesize(self, name: str, *exprs: Expr) -> str: 
        return f"({name} {' '.join([expr.accept(self) for expr in exprs])})"