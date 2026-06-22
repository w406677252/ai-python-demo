"""Tool definitions for arithmetic operations."""

from langchain.tools import tool


@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.

    Args:
        a: First integer.
        b: Second integer.
    """
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Add `a` and `b`.

    Args:
        a: First integer.
        b: Second integer.
    """
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`.

    Args:
        a: First integer.
        b: Second integer.
    """
    return a / b


tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
