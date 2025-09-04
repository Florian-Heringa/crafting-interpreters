import pytest
from pathlib import Path

from plox_lib import Scanner, Token, TokenType

class TestSimpleLexemes:

    @staticmethod
    def load_source(path: Path):
        """Helper method for loading files"""
        here = Path(__file__).resolve().parent
        source: str = ""
        with open(here / path, 'r') as src:
            source = "".join(src.readlines())
        return source
    
    def test_single_brace(self):
        """Base case test for a single brace"""
        source = TestSimpleLexemes.load_source(Path("test_programs/single_brace.lx"))
        scanner = Scanner(source)
        tokens = scanner.scanTokens()

        assert tokens == [Token(TokenType.LEFT_BRACE, "{", None, 1), Token(TokenType.EOF, "", None, 1)]

    def test_double_brace(self):
        """Base case test for a double brace"""
        source = TestSimpleLexemes.load_source(Path("test_programs/double_brace.lx"))
        scanner = Scanner(source)
        tokens = scanner.scanTokens()

        assert tokens == [Token(TokenType.LEFT_BRACE, "{", None, 1), Token(TokenType.RIGHT_BRACE, "}", None, 1), Token(TokenType.EOF, "", None, 1)]

    def test_multiple_lines_01(self):
        """Base case test for a source file with multiple lines and whitespace"""
        source = TestSimpleLexemes.load_source(Path("test_programs/multiple_lines_01.lx"))
        scanner = Scanner(source)
        tokens = scanner.scanTokens()

        assert tokens == [
            Token(TokenType.LEFT_PAREN, "(", None, 1), 
            Token(TokenType.RIGHT_PAREN, ")", None, 1), 
            Token(TokenType.LEFT_BRACE, "{", None, 2), 
            Token(TokenType.STAR, "*", None, 3), 
            Token(TokenType.MINUS, "-", None, 3), 
            Token(TokenType.PLUS, "+", None, 3), 
            Token(TokenType.SEMICOLON, ";", None, 3), 
            Token(TokenType.RIGHT_BRACE, "}", None, 4), 
            Token(TokenType.EOF, "", None, 4)
        ]

    def test_string_01(self):
        """Base case test for a single line string"""
        source = TestSimpleLexemes.load_source(Path("test_programs/string_01.lx"))
        scanner = Scanner(source)
        tokens = scanner.scanTokens()

        assert tokens == [
            Token(TokenType.STRING, "\"Hello World!\"", "Hello World!", 1), 
            Token(TokenType.SEMICOLON, ";", None, 1), 
            Token(TokenType.EOF, "", None, 1)]
        
    def test_mixed_01(self):
        """Base case test for a mixed token type source file"""
        source = TestSimpleLexemes.load_source(Path("test_programs/mixed_01.lx"))
        scanner = Scanner(source)
        tokens = scanner.scanTokens()

        assert tokens == [
            Token(TokenType.OR, "or", None, 1), 
            Token(TokenType.IDENTIFIER, "orchid", None, 1),
            Token(TokenType.EQUAL, "=", None, 1),
            Token(TokenType.NUMBER, "10", 10, 1),
            Token(TokenType.IF, "if", None, 2), 
            Token(TokenType.IDENTIFIER, "orpheus", None, 2),
            Token(TokenType.EQUAL, "=", None, 2),
            Token(TokenType.STRING, "\"Orpheus\"", "Orpheus", 2),
            Token(TokenType.WHILE, "while", None, 3), 
            Token(TokenType.IDENTIFIER, "orthogonal", None, 3),
            Token(TokenType.EQUAL, "=", None, 3),
            Token(TokenType.LEFT_PAREN, "(", None, 3),
            Token(TokenType.NUMBER, "0", 0, 3),
            Token(TokenType.COMMA, ",", None, 3),
            Token(TokenType.NUMBER, "0", 0, 3),
            Token(TokenType.RIGHT_PAREN, ")", None, 3),
            Token(TokenType.EOF, "", None, 3)]