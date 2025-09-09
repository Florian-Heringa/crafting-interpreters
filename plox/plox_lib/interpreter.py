from typing import Any
from .asts.expr import Expr, Binary, Grouping, Literal, Unary, Variable, Assign
from .asts.stmt import Stmt, Expression, Print, Var, Block, If, While
from .utils import LoxType
from .token_type import TokenType
from .token import Token
from .error import LoxRuntimeError
from .environment import Environment

# Circumvent circular import with lox.py
from . import lox
# For distinguishing the different Visitor implementations
from .asts import expr, stmt

class Interpreter(expr.Visitor[LoxType], stmt.Visitor[None]):

    def __init__(self):
        self.env = Environment()

    def interpret(self, statements: list[Stmt]) -> LoxType:
        try:
            for stmt in statements:
                self.execute(stmt)
        except LoxRuntimeError as err:
            lox.Lox.runtimeError(err)

    ############################ Visitor pattern implementation

    def visitLiteralExpr(self, expr: Literal) -> LoxType:
        """Simple, evaluates to the value contained inside"""
        return expr.value
    
    def visitLogicalExpr(self, expr: expr.Logical) -> LoxType:
        """
        Short circuiting conditional. 
        a  or b => when a is  true, don't evaluate b return a, otherwise return b
        a and b => when a is false, don't evaluate b return a, otherwise return b
        """
        left: LoxType = self.evaluate(expr.left)
        if expr.operator.token_type == TokenType.OR:
            return left if self.isTruthy(left) else self.evaluate(expr.right)
        else:
            return left if not self.isTruthy(left) else self.evaluate(expr.right)
        
    
    def visitGroupingExpr(self, expr: Grouping) -> LoxType:
        """Slightly more complicated, holds an expression inside that must be evaluated"""
        return self.evaluate(expr.expression)
    
    def visitUnaryExpr(self, expr: Unary) -> LoxType:
        """First evfaluate the contained expression, then apply the unary operator"""
        right: LoxType = self.evaluate(expr.right)

        match expr.operator.token_type:
            case TokenType.MINUS:
                # TODO: fix this type checking issue. Maybe define some helper functions in utils.py
                self.checkNumberOperand(expr.operator, right)
                return -float(right) # type: ignore
            case TokenType.BANG:
                return not self.isTruthy(right)
            
        return None

    def visitBinaryExpr(self, expr: Binary) -> LoxType:
        """Holds two expressions inside that must be evaluated, together with the operator in between"""
        left: LoxType = self.evaluate(expr.left)
        right: LoxType = self.evaluate(expr.right)

        if not isinstance(left, (float, str, bool)) or not isinstance(right, (float, str, bool)):
            return None

        match expr.operator.token_type:
            case TokenType.MINUS:
                self.checkNumberOperands(expr.operator, left, right)
                return float(left) - float(right)
            case TokenType.STAR:
                self.checkNumberOperands(expr.operator, left, right)
                return float(left) * float(right)
            case TokenType.SLASH:
                self.checkNumberOperands(expr.operator, left, right)
                return float(left) / float(right)
            case TokenType.GREATER:
                self.checkNumberOperands(expr.operator, left, right)
                return float(left) > float(right)
            case TokenType.GREATER_EQUAL:
                self.checkNumberOperands(expr.operator, left, right)
                return float(left) >= float(right)
            case TokenType.LESS:
                self.checkNumberOperands(expr.operator, left, right)
                return float(left) < float(right)
            case TokenType.LESS_EQUAL:
                self.checkNumberOperands(expr.operator, left, right)
                return float(left) <= float(right)
            case TokenType.EQUAL_EQUAL:
                return self.isEqual(left, right)
            case TokenType.BANG_EQUAL:
                return not self.isEqual(left, right)
            case TokenType.PLUS:
                if isinstance(left, float) and isinstance(right, float):
                    return float(left) + float(right)
                if isinstance(left, str) and isinstance(right, str):
                    return str(left) + str(right)
                raise LoxRuntimeError(expr.operator, "Operands must be two numbers or two strings")
    
    def visitVariableExpr(self, expr: Variable) -> LoxType:
        return self.env.get(expr.name)
    
    def visitAssignExpr(self, expr: Assign) -> LoxType:
        value: LoxType = self.evaluate(expr.value)
        self.env.assign(expr.name, value)
        return value
    
    def visitExpressionStmt(self, stmt: Expression) -> None:
        self.evaluate(stmt.expression)
        return
    
    def visitIfStmt(self, stmt: If) -> None:
        """Evaluate if statement according to the truthy rules of Lox"""
        if self.isTruthy(self.evaluate(stmt.condition)):
            self.execute(stmt.thenBranch)
        elif stmt.elseBranch is not None:
            self.execute(stmt.elseBranch)
        return
    
    def visitPrintStmt(self, stmt: Print) -> None:
        value: LoxType = self.evaluate(stmt.expression)
        print(self.stringify(value))
        return
    
    def visitVarStmt(self, stmt: Var) -> None:
        """
        By default, if no init value is given, initialise the variable value to None (or 'nil' for Lox)
        """
        value: LoxType = None
        if (stmt.initializer is not None):
            value = self.evaluate(stmt.initializer)
        
        self.env.define(stmt.name.lexeme, value)
        return
    
    def visitBlockStmt(self, stmt: Block) -> None:
        self.executeBlock(stmt.statements, Environment(self.env))
        return
    
    def visitWhileStmt(self, stmt: While) -> None:
        while self.isTruthy(self.evaluate(stmt.condition)):
            self.execute(stmt.body)
        return
    
    ######################## Helper methods

    def evaluate(self, expr: Expr) -> LoxType:
        """Used in recursive step where the expression is looped back through the tree"""
        return expr.accept(self)
    
    def execute(self, stmt: Stmt):
        """Use visitor pattern to execute statement"""
        stmt.accept(self)

    def executeBlock(self, statements: list[Stmt], environment: Environment):
        """Execute all statements in a block, using a new environment"""
        previous: Environment = self.env
        try:
            self.env = environment

            for statement in statements:
                self.execute(statement)
        finally:
            self.env = previous

    def isTruthy(self, value: LoxType) -> bool:
        """
        Check if the value is truthy. This is defined as: 
        falsey => {False, nil}
        truthy => {everything else}
        (this is the same as in Ruby)
        """
        if value == None:
            return False
        if isinstance(value, bool): 
            return bool(value)
        return True
    
    def isEqual(self, a: LoxType, b: LoxType):
        """Test equality between two LoxType values"""
        if a == None and b == None:
            return True
        if a == None:
            return False
        return a == b
    
    def stringify(self, value: LoxType) -> str:
        """Helper method for converting LoxType values to strings"""
        if value is None:
            return "nil"
        if isinstance(value, float):
            return f"{value:g}"
        return str(value)
    
    ########################## Error generation

    def checkNumberOperand(self, operator: Token, operand: LoxType):
        if isinstance(operand, float): 
            return True
        raise LoxRuntimeError(operator, "Operand must be a number")
    
    def checkNumberOperands(self, operator: Token, left: LoxType, right: LoxType):
        if isinstance(left, float) and isinstance(right, float): 
            return True
        raise LoxRuntimeError(operator, "Operands must be a number")