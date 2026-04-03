from typing import Annotated, List, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langchain_core.documents import Document

class GraphState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    