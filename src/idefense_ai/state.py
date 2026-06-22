"""State type definition for the agent graph."""

import operator

from langchain.messages import AnyMessage
from typing_extensions import Annotated, TypedDict


class MessagesState(TypedDict):
    """State of the agent graph."""

    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int
