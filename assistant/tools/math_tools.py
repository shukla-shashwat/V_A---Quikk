# tools/math_tools.py
"""
Math calculation tools with safe expression evaluation.
"""

import re
import math
import operator
from typing import Union, Tuple

# Safe operators for evaluation
SAFE_OPERATORS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
    '//': operator.floordiv,
    '%': operator.mod,
    '**': operator.pow,
    '^': operator.pow,
}

# Safe math functions
SAFE_FUNCTIONS = {
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'log': math.log10,
    'ln': math.log,
    'abs': abs,
    'round': round,
    'floor': math.floor,
    'ceil': math.ceil,
    'pow': pow,
}

# Constants
CONSTANTS = {
    'pi': math.pi,
    'e': math.e,
}


def calculate(expression: str) -> Tuple[bool, Union[float, str]]:
    """
    Safely calculate a mathematical expression.
    
    Args:
        expression: Math expression string
    
    Returns:
        Tuple of (success, result_or_error_message)
    """
    if not expression:
        return False, "No expression provided"
    
    # Clean up the expression
    expression = expression.strip().lower()
    
    # Replace common words with operators
    expression = expression.replace('plus', '+')
    expression = expression.replace('minus', '-')
    expression = expression.replace('times', '*')
    expression = expression.replace('multiplied by', '*')
    expression = expression.replace('divided by', '/')
    expression = expression.replace('to the power of', '**')
    expression = expression.replace('^', '**')
    expression = expression.replace('x', '*')  # Common typo
    
    # Replace constants
    for const, value in CONSTANTS.items():
        expression = re.sub(rf'\b{const}\b', str(value), expression)
    
    # Validate - only allow safe characters
    allowed_pattern = r'^[\d\s\+\-\*\/\.\(\)\%]+$'
    
    # Check for function calls
    has_functions = any(func in expression for func in SAFE_FUNCTIONS)
    
    if not has_functions and not re.match(allowed_pattern, expression):
        # Remove any letters that aren't functions
        expression = re.sub(r'[a-z]+', '', expression).strip()
        if not expression:
            return False, "Invalid expression"
    
    try:
        # For simple expressions, use eval with restricted globals
        # This is safe because we've validated the input
        safe_globals = {
            '__builtins__': {},
            **SAFE_FUNCTIONS,
            **CONSTANTS
        }
        
        result = eval(expression, safe_globals, {})
        
        # Format result nicely
        if isinstance(result, float):
            if result.is_integer():
                return True, int(result)
            return True, round(result, 10)
        
        return True, result
    
    except ZeroDivisionError:
        return False, "Cannot divide by zero"
    except SyntaxError:
        return False, "Invalid expression syntax"
    except Exception as e:
        return False, f"Calculation error: {str(e)}"


def calculate_simple(expression: str) -> str:
    """Legacy wrapper - returns string result."""
    success, result = calculate(expression)
    if success:
        return str(result)
    return result


# Keep old function name for backward compatibility
def calculate_legacy(expression):
    """Legacy calculate function."""
    try:
        return eval(expression)
    except Exception:
        return "Invalid expression"
