# =========== CONSTANTS ===========

DIGITS = "0123456789"


# =========== ERROR ===========

class Error:
    
    def __init__(self, pos_start, pos_end, error_name, details):

        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self):

        result = f"{self.error_name}: {self.details}"
        result = f"File {self.pos_start.file_name}, Line {self.pos_start.line + 1}"
        return result

class IllegalCharError(Error):
        
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Illegal Character", details)


class InvalidSyntaxError(Error):
        
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Illegal Syntax", details)



# =========== POSITION ===========

class Position:

    def __init__(self, index, line, column, file_name, file_text):
        self.index = index
        self.line = line
        self.column = column
        self.file_name = file_name
        self.file_text = file_text

    def advance(self, current_char = None):
        self.index += 1
        self.column += 1

        if current_char == "\n":
            self.line += 1
            self.column = 0

        return self

    def copy(self):
        return Position(self.index, self.line, self.column, self.file_name, self.file_text)
    

# =========== TOKENS ===========

# TOKEN TYPES

TT_EOF = "EOF" # End of File

TT_INT = "INT"
TT_FLOAT = "FLOAT"

TT_ADD = "ADD" # Add : +
TT_SUB = "SUB" # Subtract : -
TT_MUL = "MUL" # Multiply : *
TT_DIV = "DIV" # Divide : /
TT_MOD = "MOD" # Modulo : \

# Token Equivalences
TT_NON_VALUE_EQUIVALENCES = {"+" : TT_ADD, "-" : TT_SUB, "*" : TT_MUL, "/" : TT_DIV, "\\": TT_MOD} 

class Token:

    def __init__(self, type, value = None, pos_start = None, pos_end = None):

        self.type = type
        self.value = value
        
        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()

        if pos_end:
            self.pos_end = pos_end.copy()

    def __repr__(self):

        if self.value:
            return f"{self.type}:{self.value}"
        else:   
            return f"{self.type}"


# =========== LEXER ===========

class Lexer:

    def __init__(self, file_name, text):

        self.file_name = file_name

        # Not Reading
        self.text = text
        self.pos = Position(-1, 0, -1, file_name, text)
        self.current_char = None
        
        # Immediately starts
        self.advance()

    # Reads next character in string
    def advance(self):

        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.index] if self.pos.index < len(self.text) else None # Ends when it reaches end of string

    # Turns each character into a token
    def make_tokens(self):

        tokens = []

        while self.current_char != None:
            
            # Ignores spaces and tabs
            if self.current_char in " \t":
                self.advance()
            elif self.current_char in TT_NON_VALUE_EQUIVALENCES.keys():
                tokens.append(Token(TT_NON_VALUE_EQUIVALENCES[self.current_char], pos_start=self.pos))
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f"'{char}'")

        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens, None

    # Makes a string of digits to a integer or float
    def make_number(self):

        num_str = ""
        dot_count = 0 # To detect floats
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in DIGITS + ".":
            
            if self.current_char == ".":
                if dot_count == 1:
                    break
                
                dot_count += 1
                num_str += "."
            else:
                num_str += self.current_char

            self.advance()

        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos_start, self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos)


# =========== NODES ===========

class NumberNode:
    
    def __init__(self, token):
        self.token = token
    
    def __repr__(self):
        return f"{self.token}"

class BinaryOperationNode:
    
    def __init__(self, left_node, operator_token, right_node):
        self.left_node = left_node
        self.operator_token = operator_token
        self.right_node = right_node

    def __repr__(self):
        return f"({self.left_node}, {self.operator_token}, {self.right_node})"


# =========== PARSE RESULT ===========

class ParseResult:
    
    def __init__(self):
        self.error = None
        self.node = None
        
    def register(self, result):
        
        if isinstance(result, ParseResult):
            if result.error:
                self.error = result.error(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected '+', '-', '*', '/', or '\\'"))
            return result.node
                
        return result
        
    def success(self, node):
        
        self.node = node
        return self
        
    def failure(self, error):

        self.error = error
        return self

# =========== PARSER ===========

class Parser:
    
    def __init__(self, tokens):
        
        self.tokens = tokens
        self.token_index = -1
        self.advance()

    def advance(self):
        
        self.token_index += 1
        
        if self.token_index < len(self.tokens):
            self.current_token = self.tokens[self.token_index]

        return self.current_token
    
    def parse(self):
        
        result = self.expression()
        
        if not result.error and self.current_token.type != TT_EOF:
            return result.failure
        
        return result
    
    def factor(self):
        
        result = ParseResult()
        token = self.current_token
    
        if token.type in (TT_INT, TT_FLOAT):
            result.register(self.advance())
            return result.success(NumberNode(token))

        return result.failure(InvalidSyntaxError(token.pos_start, token.pos_end, "Expected integer or float"))

    def term(self):

        return self.binary_operation(self.factor, (TT_MUL, TT_DIV))
    
    def expression(self):
        
        return self.binary_operation(self.term, (TT_ADD, TT_SUB))    

    def binary_operation(self, function, operations):
        
        result = ParseResult()
        left = result.register(function())
        
        if result.error:
            return result
    
        while self.current_token.type in operations:
            operator_token = self.current_token
            result.register(self.advance())
            right = result.register(function())
            
            if result.error:
                return result
            
            left = BinaryOperationNode(left, operator_token, right)
            
        return result.success(left)
            

# =========== RUN ===========

def run(file_name, text):

    # Generate tokens
    lexer = Lexer(file_name, text)
    tokens, error = lexer.make_tokens()

    if error:
        return None, error

    # Generate abstract syntax tree
    parser = Parser(tokens)
    ast = parser.parse()

    return ast.node, ast.error