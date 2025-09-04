from enum import Enum

# All tokens in the Lox language, each line has a category of tokens
# 1. Single-character tokens
# 2. One- or two-character tokens
# 3. Literals
# 4. Keywords
# 5. EOF token
TokenType = Enum("TokenType", """
LEFT_PAREN RIGHT_PAREN LEFT_BRACE RIGHT_BRACE COMMA DOT MINUS PLUS SEMICOLON SLASH STAR
BANG BANG_EQUAL EQUAL EQUAL_EQUAL GREATER GREATER_EQUAL LESS LESS_EQUAL
IDENTIFIER STRING NUMBER
AND CLASS ELSE FALSE FUN FOR IF NIL OR PRINT RETURN SUPER THIS TRUE VAR WHILE 
EOF
""")
