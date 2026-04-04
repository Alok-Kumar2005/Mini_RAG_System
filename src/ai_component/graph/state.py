from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str  ## have the collection id
    Judge_response: str
    Judge_reason: str
    max_loop: int  ## to handle the loop of LLM judge and QueryNode