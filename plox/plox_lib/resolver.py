from .interpreter import Interpreter
from .asts.stmt import Stmt
from .asts.expr import Expr
from .token import Token
from .utils import FunctionType, ClassType

from .asts import expr, stmt

from . import lox

class Scoped:

    def __init__(self, resolver: "Resolver"):
        self.resolver = resolver

    def __enter__(self):
        self.resolver.scopes.append({})

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.resolver.scopes.pop()

class Resolver(stmt.Visitor[None], expr.Visitor[None]):
    """ 
    This class is used to resolve variables, functions and classes to it's correct scope.
    It contains a reference to the interpreter (where the actual scope contents are stored)
    and a map of which variables are declared and defined, dynamically generated during traversal of the
    syntax tree.

    It is run as a separate pass before the code is executed and mostly used for static analysis
    and variable resolution.
    """

    def __init__(self, interpreter: Interpreter):
        self.interpreter: Interpreter = interpreter
        # Python lists can function fine as stacks using append() and pop()
        # This structure holds a stack of scopes that are currently available. The str is the name of the 
        # variable, function or class, the bool is if it is initialised fully.
        self.scopes: list[dict[str, bool]] = []
        self.currentFunction: FunctionType = FunctionType.NONE
        self.currentClass: ClassType = ClassType.NONE

    def noScope(self) -> bool:
        return len(self.scopes) == 0
    
    def peekScope(self) -> dict[str, bool]:
        return self.scopes[-1]
    
    def numScopes(self) -> int:
        return len(self.scopes)

    def resolveStatements(self, statements: list[Stmt]):
        for statement in statements:
            self.resolveStatement(statement)

    def resolveStatement(self, statement: Stmt):
        statement.accept(self)

    def resolveExpression(self, expression: Expr):
        expression.accept(self)

    def resolveLocal(self, expr: Expr, name: Token):
        """Resolve a local variable to the nearest definition."""
        # Go through all scopes from nearest up to global to resolve a variable to the closest possible option
        for i in range(self.numScopes()):
            # If found, defer to the interpreter to get the actual resolution content
            if name.lexeme in self.scopes[self.numScopes() - 1 - i]:
                self.interpreter.resolve(expr, i)
                return
            
    def resolveFunction(self, function: stmt.Function, kind: FunctionType):

        # Keep track of in what kind of function we are alongside the scope
        enclosingFunction: FunctionType = self.currentFunction
        self.currentFunction = kind

        with Scoped(self):
            for param in function.params:
                self.declare(param)
                self.define(param)
            self.resolveStatements(function.body)

        # Restore function nesting state to before
        self.currentFunction = enclosingFunction

    def beginScope(self):
        self.scopes.append({})

    def endScope(self):
        self.scopes.pop()

    def declare(self, name: Token):
        """Declare a variable as available but uninitialised"""
        if self.noScope():
            return
        scope: dict[str, bool] = self.peekScope()
        if name.lexeme in scope:
            lox.Lox.error(name, f"Variable with this name already defined in this scope")
        scope[name.lexeme]  = False

    def define(self, name: Token):
        """Set a declared variable to initialised"""
        if self.noScope():
            return
        self.peekScope()[name.lexeme] = True    

    ############################### stmt.Visitor implementation

    def visitBlockStmt(self, stmt: stmt.Block) -> None:
        with Scoped(self):
            self.resolveStatements(stmt.statements)
        return
    
    def visitVarStmt(self, stmt: stmt.Var) -> None:
        self.declare(stmt.name)
        if stmt.initializer is not None:
            self.resolveExpression(stmt.initializer)
        self.define(stmt.name)
        return
    
    def visitFunctionStmt(self, stmt: stmt.Function) -> None:
        self.declare(stmt.name)
        self.define(stmt.name)

        self.resolveFunction(stmt, FunctionType.FUNCTION)
        return
    
    def visitExpressionStmt(self, stmt: stmt.Expression) -> None:
        self.resolveExpression(stmt.expression)
        return

    def visitIfStmt(self, stmt: stmt.If) -> None:
        self.resolveExpression(stmt.condition)
        self.resolveStatement(stmt.thenBranch)
        if stmt.elseBranch is not None:
            self.resolveStatement(stmt.elseBranch)
        return
    
    def visitPrintStmt(self, stmt: stmt.Print) -> None:
        self.resolveExpression(stmt.expression)
        return
    
    def visitReturnStmt(self, stmt: stmt.Return) -> None:
        if self.currentFunction == FunctionType.NONE:
            lox.Lox.error(stmt.keyword, "Can't return from top-level code.")
        if stmt.value is not None:
            if self.currentFunction == FunctionType.INITIALIZER:
                lox.Lox.error(stmt.keyword, "Can't return a value from an initializer.")
            self.resolveExpression(stmt.value)
        return
    
    def visitWhileStmt(self, stmt: stmt.While) -> None:
        self.resolveExpression(stmt.condition)
        self.resolveStatement(stmt.body)
        return
    
    def visitClassStmt(self, stmt: stmt.Class) -> None:
        enclosingClass: ClassType = self.currentClass
        self.currentClass = ClassType.CLASS

        self.declare(stmt.name)
        self.define(stmt.name)

        if stmt.superclass is not None:
            if stmt.name.lexeme == stmt.superclass.name.lexeme:
                lox.Lox.error(stmt.superclass.name, "Class can't inherit from itself.")

            self.currentClass = ClassType.SUBCLASS
            self.resolveExpression(stmt.superclass)

            with Scoped(self):
                # Make sure super is bound when there is a superclass
                self.peekScope()["super"] = True
                with Scoped(self):
                    self.peekScope()["this"] = True
                    for method in stmt.methods:
                        declaration: FunctionType = FunctionType.INITIALIZER if method.name.lexeme == "init" else FunctionType.METHOD
                        self.resolveFunction(method, declaration)
        else:
            with Scoped(self):
                self.peekScope()["this"] = True
                for method in stmt.methods:
                    declaration: FunctionType = FunctionType.INITIALIZER if method.name.lexeme == "init" else FunctionType.METHOD
                    self.resolveFunction(method, declaration)

        # self.beginScope()
        # # Make sure 'this' is bound for each class in the class scope
        # # similar to a closure
        # self.peekScope()["this"] = True

        # for method in stmt.methods:
        #     declaration: FunctionType = FunctionType.INITIALIZER if method.name.lexeme == "init" else FunctionType.METHOD
        #     self.resolveFunction(method, declaration)

        # self.endScope()

        # if stmt.superclass is not None:
        #     self.endScope()

        self.currentClass = enclosingClass
        return

    ############################### expr.Visitor implementation

    def visitVariableExpr(self, expr: expr.Variable) -> None:
        # In the case the variable has been declared, but not yet initialised, this is an error
        # This would be the case where the variable is used in its own initialiser
        if not self.noScope() and self.peekScope().get(expr.name.lexeme) == False:
            #print("\t", expr, "\n\t\t", self.noScope(), self.peekScope(), self.scopes)
            lox.Lox.error(expr.name, "Can't read local variable in its own initialiser")

        self.resolveLocal(expr, expr.name)
        return

    def visitAssignExpr(self, expr: expr.Assign) -> None:
        # First resolve the expression, in case it contains references to other variables
        self.resolveExpression(expr.value)
        # Then use the scope map to resolve the variable it's begin assigned to
        self.resolveLocal(expr, expr.name)
        return
    
    def visitBinaryExpr(self, expr: expr.Binary) -> None:
        self.resolveExpression(expr.left)
        self.resolveExpression(expr.right)
        return
    
    def visitCallExpr(self, expr: expr.Call) -> None:
        self.resolveExpression(expr.callee)
        for argument in expr.arguments:
            self.resolveExpression(argument)
        return
    
    def visitGetExpr(self, expr: expr.Get) -> None:
        self.resolveExpression(expr.object)
        return
    
    def visitSetExpr(self, expr: expr.Set) -> None:
        self.resolveExpression(expr.value)
        self.resolveExpression(expr.object)
        return
    
    def visitSuperExpr(self, expr: expr.Super) -> None:
        if self.currentClass == ClassType.NONE:
            lox.Lox.error(expr.keyword, "Can't use 'super' outside of a class.")
        elif self.currentClass != ClassType.SUBCLASS:
            lox.Lox.error(expr.keyword, "Can't use 'super' in a class without a subclass.")
        self.resolveLocal(expr, expr.keyword)
        return
    
    def visitThisExpr(self, expr: expr.This) -> None:
        if self.currentClass == ClassType.NONE:
            lox.Lox.error(expr.keyword, "Can't use 'this' outside of a class.")
            return
        self.resolveLocal(expr, expr.keyword)
        return
    
    def visitGroupingExpr(self, expr: expr.Grouping) -> None:
        self.resolveExpression(expr.expression)
        return
    
    def visitLiteralExpr(self, expr: expr.Literal) -> None:
        return
    
    def visitLogicalExpr(self, expr: expr.Logical) -> None:
        self.resolveExpression(expr.left)
        self.resolveExpression(expr.right)
        return
    
    def visitUnaryExpr(self, expr: expr.Unary) -> None:
        self.resolveExpression(expr.right)
        return
