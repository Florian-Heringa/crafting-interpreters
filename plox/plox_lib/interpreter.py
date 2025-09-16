from .asts.expr import Expr, Binary, Grouping, Literal, Unary, Variable, Assign, Call
from .asts.stmt import Stmt, Expression, Print, Var, Block, If, While, Function, Return
from .token_type import TokenType
from .token import Token
from .error import LoxRuntimeError
from .environment import Environment
from .lox_callable import LoxCallable
from .lox_function import LoxFunction
from .lox_class import LoxClass
from .lox_instance import LoxInstance

from . import control_flow

# Circumvent circular import with lox.py
from . import lox
# For distinguishing the different Visitor implementations
from .asts import expr, stmt

import time

class Interpreter(expr.Visitor[object], stmt.Visitor[None]):

    globals: Environment = Environment()

    def __init__(self):
        self.env: Environment = Interpreter.globals
        self.locals: dict[Expr, int] = {}

        class Clock(LoxCallable):
            def arity(self) -> int:
                return 0

            def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
                return int(time.time_ns() / 1_000_000)
            
            def __repr__(self) -> str:
                return f"<fn clock (builtin)>"

        Interpreter.globals.define("clock", Clock())

    def interpret(self, statements: list[Stmt]) -> object:
        try:
            for stmt in statements:
                self.execute(stmt)
        except LoxRuntimeError as err:
            lox.Lox.runtimeError(err)

    def resolve(self, expr: Expr, depth: int):
        self.locals[expr] = depth

    ############################ Visitor pattern implementation

    def visitLiteralExpr(self, expr: Literal) -> object:
        """Simple, evaluates to the value contained inside"""
        return expr.value
    
    def visitLogicalExpr(self, expr: expr.Logical) -> object:
        """
        Short circuiting conditional. 
        a  or b => when a is  true, don't evaluate b return a, otherwise return b
        a and b => when a is false, don't evaluate b return a, otherwise return b
        """
        left: object = self.evaluate(expr.left)
        if expr.operator.token_type == TokenType.OR:
            return left if self.isTruthy(left) else self.evaluate(expr.right)
        else:
            return left if not self.isTruthy(left) else self.evaluate(expr.right)
        
    
    def visitGroupingExpr(self, expr: Grouping) -> object:
        """Slightly more complicated, holds an expression inside that must be evaluated"""
        return self.evaluate(expr.expression)
    
    def visitUnaryExpr(self, expr: Unary) -> object:
        """First evfaluate the contained expression, then apply the unary operator"""
        right: object = self.evaluate(expr.right)

        match expr.operator.token_type:
            case TokenType.MINUS:
                # TODO: fix this type checking issue. Maybe define some helper functions in utils.py
                self.checkNumberOperand(expr.operator, right)
                return -float(right) # type: ignore
            case TokenType.BANG:
                return not self.isTruthy(right)
            
        return None

    def visitBinaryExpr(self, expr: Binary) -> object:
        """Holds two expressions inside that must be evaluated, together with the operator in between"""
        left: object = self.evaluate(expr.left)
        right: object = self.evaluate(expr.right)

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
            
    def visitCallExpr(self, expr: Call) -> object:

        callee: object = self.evaluate(expr.callee)
        arguments: list[object] = []

        for argument in expr.arguments:
            arguments.append(self.evaluate(argument))
    
        if not isinstance(callee, LoxCallable):
            raise LoxRuntimeError(expr.paren, "Can only call functions and classes.")
        
        function: LoxCallable = callee

        if len(arguments) != function.arity():
            raise LoxRuntimeError(expr.paren, f"Expected {function.arity()} arguments, but got {len(arguments)}.")
        return function.call(self, arguments)
    
    def visitGetExpr(self, expr: expr.Get) -> object:
        obj: object = self.evaluate(expr.object)
        if isinstance(obj, LoxInstance):
            return obj.get(expr.name)
        raise LoxRuntimeError(expr.name, "Only instances have properties.")
    
    def visitSetExpr(self, expr: expr.Set) -> object:
        obj: object = self.evaluate(expr.object)

        if not isinstance(obj, LoxInstance):
            raise LoxRuntimeError(expr.name, "Only instances have fields.")
        
        value: object = self.evaluate(expr.value)
        obj.set(expr.name, value)

        return value
    
    def visitThisExpr(self, expr: expr.This) -> object:
        return self.lookupVariable(expr.keyword, expr)

    def visitVariableExpr(self, expr: Variable) -> object:
        return self.lookupVariable(expr.name, expr)
    
    def visitAssignExpr(self, expr: Assign) -> object:
        value: object = self.evaluate(expr.value)
        distance: int | None = self.locals.get(expr)
        if distance is not None:
            self.env.assignAt(distance, expr.name, value)
        else:
            self.globals.assign(expr.name, value)
        return value
    
    def visitExpressionStmt(self, stmt: Expression) -> None:
        self.evaluate(stmt.expression)
        return
    
    def visitFunctionStmt(self, stmt: Function) -> None:
        """Function definition, the function gets passed the current environment as a closure at the moment it is declared. 
        And gets defined in the current environment scope."""
        function: LoxFunction = LoxFunction(stmt, self.env)
        self.env.define(stmt.name.lexeme, function)
        return
    
    def visitIfStmt(self, stmt: If) -> None:
        """Evaluate if statement according to the truthy rules of Lox"""
        if self.isTruthy(self.evaluate(stmt.condition)):
            self.execute(stmt.thenBranch)
        elif stmt.elseBranch is not None:
            self.execute(stmt.elseBranch)
        return
    
    def visitPrintStmt(self, stmt: Print) -> None:
        value: object = self.evaluate(stmt.expression)
        print(self.stringify(value))
        return
    
    def visitReturnStmt(self, stmt: stmt.Return) -> None:
        value: object = None
        if stmt.value is not None:
            value = self.evaluate(stmt.value)
        raise control_flow.Return(value)
    
    def visitVarStmt(self, stmt: Var) -> None:
        """
        By default, if no init value is given, initialise the variable value to None (or 'nil' for Lox)
        """
        value: object = None
        if (stmt.initializer is not None):
            value = self.evaluate(stmt.initializer)
        
        self.env.define(stmt.name.lexeme, value)
        return
    
    def visitBlockStmt(self, stmt: Block) -> None:
        self.executeBlock(stmt.statements, Environment(self.env))
        return
    
    def visitClassStmt(self, stmt: stmt.Class) -> None:
        self.env.define(stmt.name.lexeme, None)

        methods: dict[str, LoxFunction] = {}
        for method in stmt.methods:
            function: LoxFunction = LoxFunction(method, self.env)
            methods[method.name.lexeme] = function

        newClass: LoxClass = LoxClass(stmt.name.lexeme, methods)
        self.env.assign(stmt.name, newClass)
        return
    
    def visitWhileStmt(self, stmt: While) -> None:
        while self.isTruthy(self.evaluate(stmt.condition)):
            self.execute(stmt.body)
        return
    
    ######################## Helper methods

    def lookupVariable(self, name: Token, expr: Expr) -> object:
        """
        After a Resolver pass we know where the resolved variable should be, so we can traverse
        the stack of scopes and find the correct resolution. If it is not found (no distance value is known),
        try to find it in the global scope.
        """
        distance: int | None = self.locals.get(expr)
        if distance is not None:
            return self.env.getAt(name.lexeme, distance)
        else:
            return self.globals.get(name)

    def evaluate(self, expr: Expr) -> object:
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

    def isTruthy(self, value: object) -> bool:
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
    
    def isEqual(self, a: object, b: object):
        """Test equality between two object values"""
        if a == None and b == None:
            return True
        if a == None:
            return False
        return a == b
    
    def stringify(self, value: object) -> str:
        """Helper method for converting object values to strings"""
        if value is None:
            return "nil"
        if isinstance(value, float):
            return f"{value:g}"
        return str(value)
    
    ########################## Error generation

    def checkNumberOperand(self, operator: Token, operand: object):
        if isinstance(operand, float): 
            return True
        raise LoxRuntimeError(operator, "Operand must be a number")
    
    def checkNumberOperands(self, operator: Token, left: object, right: object):
        if isinstance(left, float) and isinstance(right, float): 
            return True
        raise LoxRuntimeError(operator, "Operands must be a number")