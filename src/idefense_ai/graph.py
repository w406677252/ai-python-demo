"""Agent graph: nodes, routing logic, and compilation."""

from typing import Literal

from langchain.messages import SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph

from .llm import model_with_tools
from .state import MessagesState
from .tools import tools_by_name

# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def llm_call(state: MessagesState) -> dict:
    """LLM node — decides whether to call a tool or respond directly.

    Args:
        state: Current graph state with messages and call count.

    Returns:
        Updated state with the new LLM response and incremented call count.
    """
    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with "
                        "performing arithmetic on a set of inputs."
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def tool_node(state: MessagesState) -> dict:
    """Tool node — executes tool calls requested by the LLM.

    Args:
        state: Current graph state containing the last message with tool calls.

    Returns:
        Dict with a list of ``ToolMessage`` results.
    """
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool_instance = tools_by_name[tool_call["name"]]
        observation = tool_instance.invoke(tool_call["args"])
        result.append(
            ToolMessage(content=observation, tool_call_id=tool_call["id"])
        )
    return {"messages": result}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def should_continue(state: MessagesState) -> Literal["tool_node", "__end__"]:
    """Route to the tool node when the LLM made tool calls, otherwise end.

    Args:
        state: Current graph state.

    Returns:
        ``"tool_node"`` if the last message contains tool calls,
        otherwise ``END``.
    """
    last_message = state["messages"][-1]
    return "tool_node" if last_message.tool_calls else END


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

agent_builder = StateGraph(MessagesState)
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END],
)
agent_builder.add_edge("tool_node", "llm_call")

agent = agent_builder.compile()
