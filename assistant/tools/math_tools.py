# tools/math_tools.py

def calculate(expression):
    try:
        return eval(expression)
    except Exception:
        return "Invalid expression"
