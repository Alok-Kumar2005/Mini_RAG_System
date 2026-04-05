import os
import asyncio
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode
from src.ai_component.graph.state import GraphState
from src.ai_component.graph.nodes import Nodes
from src.ai_component.graph.edges import route_after_query, route_after_judge
from src.ai_component.tools.rag_tool import pdf_search_tool
from src.ai_component.tools.web_tool import web_tool

from src.logger import logging
from src.exceptions import CustomException

tools_node = ToolNode(tools=[pdf_search_tool, web_tool])

def Workflow(checkpointer = None):
    builder = StateGraph(
        GraphState,
        input=GraphState,
        config_schema=None,
    )
    my_nodes = Nodes()

    # add nodes
    builder.add_node("query_node", my_nodes.QueryNode)
    builder.add_node("judge_node", my_nodes.LLMJudgeNode)
    builder.add_node("summarizer_node", my_nodes.summarizer)
    builder.add_node("tools", tools_node)

    # add edges
    builder.add_edge(START, "query_node")
    builder.add_conditional_edges(
        "query_node",
        route_after_query,
        {
            "tools": "tools",
            "judge_node": "judge_node"
        }
    )
    builder.add_edge("tools", "query_node")

    builder.add_conditional_edges(
        "judge_node",
        route_after_judge,
        {
            "query_node": "query_node",
            "summarizer_node": "summarizer_node",
            "__end__": END,
        },
    )
    builder.add_edge("summarizer_node", END)

    return builder.compile(checkpointer=checkpointer)


def save_graph_image():
    graph = Workflow()
    drawable = graph.get_graph()
    png_bytes = drawable.draw_mermaid_png()
    with open("workflow_graph.png", "wb") as f:
        f.write(png_bytes)

if __name__ == "__main__":
    save_graph_image()