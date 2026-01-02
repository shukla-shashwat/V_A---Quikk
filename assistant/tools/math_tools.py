"""math_tools.py
Small math helpers used by the assistant.
"""
from typing import Union


def add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    return a + b


def multiply(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    return a * b
