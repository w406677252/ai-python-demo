"""Entry layer — CLI entry point for ``idefense_ai``.

This is the top-most layer of the call chain.  It handles user interaction
and delegates to the orchestration layer (``graph``).
"""

from langchain.messages import HumanMessage

from .graph import agent


def main() -> None:
    """Run the arithmetic agent with a hardcoded query."""
    messages = [HumanMessage(content="Add 3 and 4.")]
    result = agent.invoke({"messages": messages})
    for m in result["messages"]:
        m.pretty_print()


if __name__ == "__main__":
    main()
