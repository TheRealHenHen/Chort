import string

# =========== CONSTANTS ===========

DIGITS = "0123456789"
LETTERS = string.ascii_letters
RESERVED_KEYWORDS = "deFgiopstT"

# =========== ERROR ===========

class Error:
    
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self):
        result = f"{self.error_name}: {self.details}\n"
        result += f"File {self.pos_start.file_name}, line {self.pos_start.line + 1}"
        return result

class IllegalCharError(Error):
        
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Illegal Character", details)

class InvalidSyntaxError(Error):
        
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Illegal Syntax", details)

class RuntimeError(Error):
        
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, "Runtime Error", details)
        self.context = context
    
    def as_string(self):
        result = self.generate_traceback()
        result += f"{self.error_name}: {self.details}"
        return result

    def generate_traceback(self):

        result = ""
        pos = self.pos_start
        context = self.context

        while context:
            result = f"     File {pos.file_name}, line {pos.line + 1}, in {context.display_name}\n" + result
            pos = context.parent_entry_pos
            context = context.parent
            
        return "Traceback!:\n" + result

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
TT_BOOL = "BOOL"
TT_STRING = "STRING"

TT_EE = "EE" # Equal to : =
TT_NE = "NE" # Not equal to : !
TT_LT = "LT" # Less than : <
TT_GT = "GT" # Greater than : >

TT_AND = "AND" # And : &
TT_OR = "OR" # Or : |
TT_NOT = "NOT" # Not : ~

TT_ADD = "ADD" # Add : +
TT_SUB = "SUB" # Subtract : -
TT_MUL = "MUL" # Multiply : *
TT_DIV = "DIV" # Divide : /
TT_MOD = "MOD" # Modulo : \
    
TT_LPAREN = "LPAREN"    
TT_RPAREN = "RPAREN"    

TT_IDENTIFIER = "IDENTIFIER" # Variable name    
TT_KEYWORD = "KEYWORD"    
    
# Token Equivalences
TT_NON_VALUE_EQ = {"+" : TT_ADD, "-" : TT_SUB, "*" : TT_MUL, "/" : TT_DIV, "\\": TT_MOD,
                   "=" : TT_EE, "!" : TT_NE, "<" : TT_LT, ">" : TT_GT,
                   "&" : TT_AND, "|" : TT_OR, "~" : TT_NOT} 
TT_PARENTHESIS_EQ = {"(" : TT_LPAREN, ")" : TT_RPAREN}

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

    def matches(self, type, value):
        
        return self.type == type and self.value == value

    def __repr__(self):

        if self.value != None:
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

            elif self.current_char in TT_NON_VALUE_EQ.keys():
                tokens.append(Token(TT_NON_VALUE_EQ[self.current_char], pos_start=self.pos))
                self.advance()

            elif self.current_char in TT_PARENTHESIS_EQ.keys():
                tokens.append(Token(TT_PARENTHESIS_EQ[self.current_char], pos_start=self.pos))
                self.advance()

            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
                
            elif self.current_char in LETTERS:
                tokens.append(self.make_identifier())
                
            elif self.current_char == '"':
                token, error = self.make_string()
                if error: return [], error
                tokens.append(token)
                
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

    # Makes everything between two quotes into a string, spaces included
    def make_string(self):
        
        string = ""
        pos_start = self.pos.copy()
        escape_character = False # For things like \n or \"
        escape_characters = {"n" : "\n", "t" : "\t"}
        
        self.advance()
        
        while self.current_char != None and (self.current_char != '"' or escape_character):
            
            if escape_character:
                string += escape_characters.get(self.current_char, self.current_char)
                escape_character = False
            elif self.current_char == "\\":
                escape_character = True
            else:
                string += self.current_char
            
            self.advance()
        
        if self.current_char != '"':
            return None, InvalidSyntaxError(pos_start, self.pos, "Close your string!")
        
        self.advance()
        
        return Token(TT_STRING, string, pos_start, self.pos), None

    def make_identifier(self):
        
        identifier_string = self.current_char
        pos_start = self.pos.copy()
        self.advance()

        # T and F are booleans
        if identifier_string == "T":
            return Token(TT_BOOL, True, pos_start, self.pos)
        elif identifier_string == "F":
            return Token(TT_BOOL, False, pos_start, self.pos)

        token_type = TT_KEYWORD if identifier_string in RESERVED_KEYWORDS else TT_IDENTIFIER
        
        return Token(token_type, identifier_string, pos_start, self.pos)

# =========== NODES ===========

class NumberNode:
    
    def __init__(self, token):
        self.token = token
    
        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end
    
    def __repr__(self):
        return f"{self.token}"

class BooleanNode:
    
    def __init__(self, token):
        self.token = token
    
        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end
    
    def __repr__(self):
        return f"{self.token}"

class StringNode:
    
    def __init__(self, token):
        self.token = token
    
        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end
    
    def __repr__(self):
        return f"{self.token}"

class VariableAccessNode:
    
    def __init__(self, variable_name_token):
        
        self.variable_name_token = variable_name_token
        
        self.pos_start = self.variable_name_token.pos_start
        self.pos_end = self.variable_name_token.pos_end

    def __repr__(self):
        return f"{self.variable_name_token}"

class VariableAssignNode:
    
    def __init__(self, variable_name_token, value_node):
        
        self.variable_name_token = variable_name_token
        self.value_node = value_node
        
        self.pos_start = self.variable_name_token.pos_start
        self.pos_end = self.value_node.pos_end

    def __repr__(self):
        return f"({self.variable_name_token}, {self.value_node})"

class DebugStartNode:

    def __init__(self, keyword_token, variable_name_token):
        self.keyword_token = keyword_token
        self.variable_name_token = variable_name_token

        self.pos_start = self.keyword_token.pos_start
        self.pos_end = self.variable_name_token.pos_end

    def __repr__(self):
        return f"({self.keyword_token}, {self.variable_name_token})"

class DebugStopNode:

    def __init__(self, keyword_token, variable_name_token):
        self.keyword_token = keyword_token
        self.variable_name_token = variable_name_token

        self.pos_start = self.keyword_token.pos_start
        self.pos_end = self.variable_name_token.pos_end

    def __repr__(self):
        return f"({self.keyword_token}, {self.variable_name_token})"

class BinaryOperatorNode:
    
    def __init__(self, left_node, operator_token, right_node):
        self.left_node = left_node
        self.operator_token = operator_token
        self.right_node = right_node

        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self):
        return f"({self.left_node}, {self.operator_token}, {self.right_node})"

class UnaryOperatorNode:
    
    def __init__(self, operator_token, node):
        self.operator_token = operator_token
        self.node = node
        
        self.pos_start = self.operator_token.pos_start
        self.pos_end = node.pos_end
        
    def __repr__(self):
        return f"({self.operator_token}, {self.node})"

class PrintNode:
    
    def __init__(self, keyword_token, value_node):
        self.keyword_token = keyword_token
        self.value_node = value_node
        
        self.pos_start = self.keyword_token.pos_start
        self.pos_end = self.value_node.pos_end
        
    def __repr__(self):
        return f"({self.keyword_token}, {self.value_node})"

class InputNode:
    
    def __init__(self, variable_name_token, keyword_token):
        self.variable_name_token = variable_name_token
        self.keyword_token = keyword_token
        
        self.pos_start = self.variable_name_token.pos_start
        self.pos_end = self.keyword_token.pos_end
        
    def __repr__(self):
        return f"({self.variable_name_token}, {self.keyword_token})"

class IfNode:
    
    def __init__(self, cases, else_case):
        self.cases = cases # List of (condition node, statement node)
        self.else_case = else_case
        
        self.pos_start = self.cases[0][0].pos_start
        
        if self.else_case:
            self.pos_end = self.else_case.pos_end
        else:
            self.pos_end = self.cases[-1][1].pos_end
        
    def __repr__(self):
        return f"({self.cases}, {self.else_case})"

class StatementsNode:
    
    def __init__(self, statement_nodes):
        self.statement_nodes = statement_nodes
        
        self.pos_start = self.statement_nodes[0].pos_start
        self.pos_end = self.statement_nodes[-1].pos_end
        
    def __repr__(self):
        return f"{self.statement_nodes}"

# =========== PARSE RESULT ===========

class ParseResult:
    
    def __init__(self):
        self.error = None
        self.node = None
        self.advance_count = 0

    def register_advancement(self):
        self.advance_count += 1
        
    def register(self, result):    
        self.advance_count += result.advance_count
        if result.error:
            self.error = result.error
        return result.node
        
    def success(self, node):
        self.node = node
        return self
        
    def failure(self, error):
        if not self.error or self.advance_count == 0:
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
        
        return self.statements()

    # Statements are chained on one line with no spaces or separators, like a5b6
    def statements(self):
        
        result = ParseResult()
        statements = []
        
        statements.append(result.register(self.statement()))
        
        if result.error:
            return result
        
        while self.current_token.type != TT_EOF:
            
            statements.append(result.register(self.statement()))
            
            if result.error:
                return result
        
        return result.success(StatementsNode(statements))

    # A statement is a command like p5 or sx, or just an expression
    def statement(self):
        
        result = ParseResult()
        
        # Print like p5
        if self.current_token.matches(TT_KEYWORD, "p"):
            
            keyword_token = self.current_token
            result.register_advancement()
            self.advance()
            
            # No assignment inside print, so pab6 is print a then b6
            value_node = result.register(self.or_expression())
            
            if result.error:
                return result
            
            return result.success(PrintNode(keyword_token, value_node))

        # Start debugging a variable like dx
        if self.current_token.matches(TT_KEYWORD, "d"):

            keyword_token = self.current_token
            result.register_advancement()
            self.advance()

            if self.current_token.type != TT_IDENTIFIER:
                return result.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "I didn't find a variable name after 'd'!"))

            variable_name = self.current_token
            result.register_advancement()
            self.advance()

            return result.success(DebugStartNode(keyword_token, variable_name))

        # Stop debugging a variable like gx
        if self.current_token.matches(TT_KEYWORD, "g"):

            keyword_token = self.current_token
            result.register_advancement()
            self.advance()

            if self.current_token.type != TT_IDENTIFIER:
                return result.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "I didn't find a variable name after 'g'!"))

            variable_name = self.current_token
            result.register_advancement()
            self.advance()

            return result.success(DebugStopNode(keyword_token, variable_name))
        
        # Input like xs
        if self.current_token.type == TT_IDENTIFIER and self.token_index + 1 < len(self.tokens) and self.tokens[self.token_index + 1].matches(TT_KEYWORD, "s"):
            
            variable_name = self.current_token
            result.register_advancement()
            self.advance()
            
            keyword_token = self.current_token
            result.register_advancement()
            self.advance()
            
            return result.success(InputNode(variable_name, keyword_token))
        
        # If statement like i3=4tp1o4=5tp2ep3
        if self.current_token.matches(TT_KEYWORD, "i"):
            return self.if_statement()
        
        return self.expression()

    # i<condition>t<statement> then any number of o<condition>t<statement> then an optional e<statement>
    def if_statement(self):
        
        result = ParseResult()
        cases = []
        else_case = None
        
        # The first case starts with i, the rest start with o
        keyword = "i"
        
        while self.current_token.matches(TT_KEYWORD, keyword):
            
            result.register_advancement()
            self.advance()
            
            condition = result.register(self.or_expression())
            
            if result.error:
                return result
            
            if not self.current_token.matches(TT_KEYWORD, "t"):
                return result.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "I didn't find a 't' after the condition!"))
            
            result.register_advancement()
            self.advance()
            
            statement = result.register(self.statement())
            
            if result.error:
                return result
            
            cases.append((condition, statement))
            keyword = "o"
        
        if self.current_token.matches(TT_KEYWORD, "e"):
            
            result.register_advancement()
            self.advance()
            
            else_case = result.register(self.statement())
            
            if result.error:
                return result
        
        return result.success(IfNode(cases, else_case))
    
    def factor(self):
        
        result = ParseResult()
        token = self.current_token
        
        # Unary operation like -5
        if token.type in (TT_ADD, TT_SUB):
            
            result.register_advancement()
            self.advance()
            factor = result.register(self.factor())
            
            if result.error:
                return result

            return result.success(UnaryOperatorNode(token, factor))
    
        # Normal integer or float like 5
        elif token.type in (TT_INT, TT_FLOAT):
            result.register_advancement()
            self.advance()
            return result.success(NumberNode(token))

        # Strings
        elif token.type == TT_STRING:
            result.register_advancement()
            self.advance()
            return result.success(StringNode(token))

        # Booleans
        elif token.type == TT_BOOL:
            result.register_advancement()
            self.advance()
            return result.success(BooleanNode(token))

        # Parenthesis with expression inside
        elif token.type == TT_LPAREN:
            
            result.register_advancement()
            self.advance()
            expression = result.register(self.expression())
            
            if result.error:
                return result
            
            if self.current_token.type == TT_RPAREN:
                result.register_advancement()
                self.advance()
                return result.success(expression)
            else:
                return result.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Close your parenthesis!"))

        # Variable
        elif token.type == TT_IDENTIFIER:
            result.register_advancement()
            self.advance()
            return result.success(VariableAccessNode(token))

        return result.failure(InvalidSyntaxError(token.pos_start, token.pos_end, "I didn't find an integer, float, string, boolean, or identifier! >:("))

    def term(self):

        return self.binary_operation(self.factor, (TT_MUL, TT_DIV, TT_MOD))

    def arithmetic_expression(self):

        return self.binary_operation(self.term, (TT_ADD, TT_SUB))

    def comp_expression(self):

        result = ParseResult()

        # Not operation like ~T
        if self.current_token.type == TT_NOT:

            operator_token = self.current_token
            result.register_advancement()
            self.advance()

            node = result.register(self.comp_expression())

            if result.error:
                return result

            return result.success(UnaryOperatorNode(operator_token, node))

        return self.binary_operation(self.arithmetic_expression, (TT_EE, TT_NE, TT_LT, TT_GT))

    def and_expression(self):

        return self.binary_operation(self.comp_expression, (TT_AND,))
    
    def or_expression(self):

        return self.binary_operation(self.and_expression, (TT_OR,))
    
    def expression(self):
        
        result = ParseResult()
        
        if self.current_token.type == TT_IDENTIFIER and self.token_index + 1 < len(self.tokens):
            
            next_token = self.tokens[self.token_index + 1]
            
            if next_token.type in (TT_INT, TT_FLOAT, TT_STRING, TT_BOOL, TT_IDENTIFIER, TT_LPAREN, TT_NOT):
            
                variable_name = self.current_token
                result.register_advancement()
                self.advance()

                expression = result.register(self.expression())
            
                if result.error:
                    return result
            
                return result.success(VariableAssignNode(variable_name, expression))
            
        node = result.register(self.or_expression())
        
        if result.error:
            return result.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "I didn't find an integer, float, string, boolean, identifier or keyword! >:("))
        
        return result.success(node)    

    def binary_operation(self, function, operations):
        
        result = ParseResult()
        left = result.register(function())
        
        if result.error:
            return result
    
        while self.current_token.type in operations:
            operator_token = self.current_token
            result.register_advancement()
            self.advance()
            right = result.register(function())
            
            if result.error:
                return result
            
            left = BinaryOperatorNode(left, operator_token, right)
            
        return result.success(left)
            

# =========== RUNTIME RESULT ===========

class RuntimeResult:
    
    def __init__(self):
        
        self.value = None
        self.error = None
        
    def register(self, result):
        
        if result.error:
            self.error = result.error
        
        return result.value

    def success(self, value):

        self.value = value
        return self
        
    def failure(self, error):
    
        self.error = error
        return self

# =========== VALUES ===========

class Value:

    def set_pos(self, pos_start = None, pos_end = None):
        
        self.pos_start = pos_start
        self.pos_end = pos_end
        
        return self
    
    def set_context(self, context = None):
        self.context = context
        return self

    # Every operation is illegal unless the value type has its own version of it
    def added_to(self, other):
        return None, self.illegal_operation(other)

    def subtracted_by(self, other):
        return None, self.illegal_operation(other)

    def multiplied_to(self, other):
        return None, self.illegal_operation(other)

    def divided_by(self, other):
        return None, self.illegal_operation(other)

    def modulo_by(self, other):
        return None, self.illegal_operation(other)

    def equal_to(self, other):
        return None, self.illegal_operation(other)

    def not_equal_to(self, other):
        return None, self.illegal_operation(other)

    def less_than(self, other):
        return None, self.illegal_operation(other)

    def greater_than(self, other):
        return None, self.illegal_operation(other)

    def anded_by(self, other):
        return None, self.illegal_operation(other)

    def ored_by(self, other):
        return None, self.illegal_operation(other)

    def notted(self):
        return None, self.illegal_operation()

    def illegal_operation(self, other = None):

        if other == None:
            other = self

        return RuntimeError(self.pos_start, other.pos_end, "I can't do that operation on those values!", self.context)

class Number(Value):
    
    def __init__(self, value):
        
        self.value = value
        self.set_pos()
        self.set_context()

    def added_to(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None

    def subtracted_by(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        
    def multiplied_to(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None
        
    def divided_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RuntimeError(other.pos_start, other.pos_end, "We don't know what divided by zero is yet!", self.context)
            return Number(self.value / other.value).set_context(self.context), None

    def modulo_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RuntimeError(other.pos_start, other.pos_end, "We don't know what modulo zero is yet!", self.context)
            return Number(self.value % other.value).set_context(self.context), None

    def equal_to(self, other):
        if isinstance(other, Number):
            return Boolean(self.value == other.value).set_context(self.context), None

    def not_equal_to(self, other):
        if isinstance(other, Number):
            return Boolean(self.value != other.value).set_context(self.context), None

    def less_than(self, other):
        if isinstance(other, Number):
            return Boolean(self.value < other.value).set_context(self.context), None

    def greater_than(self, other):
        if isinstance(other, Number):
            return Boolean(self.value > other.value).set_context(self.context), None

    def __repr__(self):
        return str(self.value)

class String(Value):

    def __init__(self, value):

        self.value = value
        self.set_pos()
        self.set_context()

    def added_to(self, other):
        if isinstance(other, String):
            return String(self.value + other.value).set_context(self.context), None

    def equal_to(self, other):
        if isinstance(other, String):
            return Boolean(self.value == other.value).set_context(self.context), None

    def not_equal_to(self, other):
        if isinstance(other, String):
            return Boolean(self.value != other.value).set_context(self.context), None

    def __repr__(self):
        return self.value

class Boolean(Value):

    def __init__(self, value):

        self.value = value
        self.set_pos()
        self.set_context()

    def equal_to(self, other):
        if isinstance(other, Boolean):
            return Boolean(self.value == other.value).set_context(self.context), None

    def not_equal_to(self, other):
        if isinstance(other, Boolean):
            return Boolean(self.value != other.value).set_context(self.context), None

    def anded_by(self, other):
        if isinstance(other, Boolean):
            return Boolean(self.value and other.value).set_context(self.context), None

    def ored_by(self, other):
        if isinstance(other, Boolean):
            return Boolean(self.value or other.value).set_context(self.context), None

    def notted(self):
        return Boolean(not self.value).set_context(self.context), None

    def __repr__(self):
        return "T" if self.value else "F"

# =========== CONTEXT ===========

class Context:
    
    def __init__(self, display_name, parent = None, parent_entry_pos = None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None

# =========== SYMBOL TABLE ===========

class SymbolTable:
    
    def __init__(self):
        self.symbols = {}
        self.parent = None
        
    def get(self, name):
        
        value = self.symbols.get(name, None)
        
        if value == None and self.parent:
            return self.parent.get(name)
        
        return value
    
    def set(self, name, value):
        self.symbols[name] = value
    
    def remove(self, name):
        del self.symbols[name]    


# =========== INTERPRETER ===========

class Interpreter:

    def __init__(self):
        self.watched_vars = set()
    
    def visit(self, node, context):
        
        method_name = f"visit_{type(node).__name__}"

        method = getattr(self, method_name, self.no_visit_method)
        
        return method(node, context)

    def no_visit_method(self, node, context):
        
        raise Exception(f"I can't visit that method! ({type(node).__name__} doesn't exist bro)")

    def assign_variable(self, variable_name, value, context):

        old_value = context.symbol_table.get(variable_name)
        context.symbol_table.set(variable_name, value)

        if variable_name in self.watched_vars:
            if old_value is None or type(old_value) != type(value) or old_value.value != value.value:
                debug_str_node = StringNode(Token(TT_STRING, f"{variable_name}: {value}", pos_start=value.pos_start, pos_end=value.pos_end))
                print_node = PrintNode(Token(TT_KEYWORD, "p", pos_start=value.pos_start, pos_end=value.pos_end), debug_str_node)
                self.visit_PrintNode(print_node, context)

    def visit_StatementsNode(self, node, context):
        
        result = RuntimeResult()
        value = None
        
        for statement_node in node.statement_nodes:
            
            value = result.register(self.visit(statement_node, context))
            
            if result.error:
                return result
        
        # The value of the last statement is the value of the whole line
        return result.success(value)

    def visit_DebugStartNode(self, node, context):

        variable_name = node.variable_name_token.value
        self.watched_vars.add(variable_name)
        return RuntimeResult().success(None)

    def visit_DebugStopNode(self, node, context):

        variable_name = node.variable_name_token.value
        self.watched_vars.discard(variable_name)
        return RuntimeResult().success(None)

    def visit_PrintNode(self, node, context):
        
        result = RuntimeResult()
        
        value = result.register(self.visit(node.value_node, context))
        
        if result.error:
            return result
        
        print(value)
        
        return result.success(None)

    def visit_InputNode(self, node, context):
        
        result = RuntimeResult()
        variable_name = node.variable_name_token.value
        
        text = input().strip()
        
        # Numbers and T or F are read as those, anything else is a string
        if text == "T":
            value = Boolean(True)
        elif text == "F":
            value = Boolean(False)
        else:
            try:
                value = Number(int(text))
            except ValueError:
                try:
                    value = Number(float(text))
                except ValueError:
                    value = String(text)
        
        value.set_context(context).set_pos(node.pos_start, node.pos_end)
        self.assign_variable(variable_name, value, context)
        
        return result.success(None)

    def visit_IfNode(self, node, context):
        
        result = RuntimeResult()
        
        for condition_node, statement_node in node.cases:
            
            condition = result.register(self.visit(condition_node, context))
            
            if result.error:
                return result
            
            if not isinstance(condition, Boolean):
                return result.failure(RuntimeError(condition_node.pos_start, condition_node.pos_end, "The condition has to be T or F!", context))
            
            if condition.value:
                
                value = result.register(self.visit(statement_node, context))
                
                if result.error:
                    return result
                
                return result.success(value)
        
        if node.else_case:
            
            value = result.register(self.visit(node.else_case, context))
            
            if result.error:
                return result
            
            return result.success(value)
        
        return result.success(None)

    def visit_VariableAccessNode(self, node, context):

        result = RuntimeResult()
        variable_name = node.variable_name_token.value
        value = context.symbol_table.get(variable_name)

        if not value:
            return result.failure(RuntimeError(node.pos_start, node.pos_end, f"'{variable_name}' isn't defined yet!", context))

        value = value.copy() if hasattr(value, "copy") else value
        return result.success(value.set_pos(node.pos_start, node.pos_end).set_context(context))

    def visit_VariableAssignNode(self, node, context):

        result = RuntimeResult()
        variable_name = node.variable_name_token.value
        value = result.register(self.visit(node.value_node, context))

        if result.error:
            return result

        self.assign_variable(variable_name, value, context)
        return result.success(value)

    def visit_NumberNode(self, node, context):
        
        return RuntimeResult().success(Number(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end))

    def visit_StringNode(self, node, context):
        
        return RuntimeResult().success(String(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end))

    def visit_BooleanNode(self, node, context):
        
        return RuntimeResult().success(Boolean(node.token.value).set_context(context).set_pos(node.pos_start, node.pos_end))

    def visit_UnaryOperatorNode(self, node, context):

        response = RuntimeResult()
        operand = response.register(self.visit(node.node, context))

        if response.error:
            return response

        error = None

        if node.operator_token.type == TT_SUB:
            operand, error = operand.multiplied_to(Number(-1))
        elif node.operator_token.type == TT_NOT:
            operand, error = operand.notted()

        if error:
            return response.failure(error)

        return response.success(operand.set_pos(node.pos_start, node.pos_end))
        
    def visit_BinaryOperatorNode(self, node, context):
        
        response = RuntimeResult()
        
        left = response.register(self.visit(node.left_node, context))
        
        if response.error:
            return response
        
        right = response.register(self.visit(node.right_node, context))

        if response.error:
            return response

        operator = node.operator_token.type

        # Both sides need to be the same type, like 1=T doesn't make sense
        if type(left) != type(right):
            return response.failure(RuntimeError(node.pos_start, node.pos_end, "Those two values aren't the same type!", context))

        if operator == TT_ADD:
            result, error = left.added_to(right)
        elif operator == TT_SUB:
            result, error = left.subtracted_by(right)
        elif operator == TT_MUL:
            result, error = left.multiplied_to(right)
        elif operator == TT_DIV:
            result, error = left.divided_by(right)
        elif operator == TT_MOD:
            result, error = left.modulo_by(right)
        elif operator == TT_EE:
            result, error = left.equal_to(right)
        elif operator == TT_NE:
            result, error = left.not_equal_to(right)
        elif operator == TT_LT:
            result, error = left.less_than(right)
        elif operator == TT_GT:
            result, error = left.greater_than(right)
        elif operator == TT_AND:
            result, error = left.anded_by(right)
        elif operator == TT_OR:
            result, error = left.ored_by(right)

        if error:
            return response.failure(error)

        return response.success(result.set_pos(node.pos_start, node.pos_end))


# =========== RUN ===========

global_symbol_table = SymbolTable()

def run(file_name, text):

    lexer = Lexer(file_name, text)
    tokens, error = lexer.make_tokens()
    if error: return None, error

    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error: return None, ast.error

    interpreter = Interpreter()
    context = Context("<program>")
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)
    interpreter.watched_vars.clear()

    return result.value, result.error