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

def Workflow():
    builder = StateGraph(GraphState)
    my_nodes = Nodes()

    # add nodes
    builder.add_node("query_node", my_nodes.QueryNode)
    builder.add_node("judge_node", my_nodes.LLMJudgeNode)
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
            "__end__": END
        }
    )

    return builder.compile()


import asyncio
from langchain_core.messages import HumanMessage
async def run_full_workflow_test():
    print("--- 1. Initializing the Agentic RAG Workflow ---")
    app = Workflow() 
    inputs = {
        "messages": [HumanMessage(content="What does the document say about architecture?")],
        "session_id": "doc_user_aveek_123"
    }
    
    print(f"\nUser Query: {inputs['messages'][0].content}")
    print("--- 2. Running Graph (Please wait...) ---\n")
    result = await app.ainvoke(inputs)
    
    print("\n==========================================")
    print("           FINAL CHAT HISTORY             ")
    print("==========================================")
    
    for msg in result.get("messages", []):
        msg_type = msg.__class__.__name__
        
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            print(f"🤖 {msg_type} [ACTION]: Requested Tool -> '{msg.tool_calls[0]['name']}'")
            print(f"   ↳ Args: {msg.tool_calls[0]['args']}")
            
        elif msg_type == "ToolMessage":
            # Truncating the output so it doesn't flood your console
            content_preview = msg.content[:150].replace('\n', ' ') + "..." if len(msg.content) > 150 else msg.content
            print(f"🔧 {msg_type} [RESULT]: {content_preview}")
            
        # Normal conversational message (Human, AI text, or Feedback)
        else:
            prefix = "👤 Human" if msg_type == "HumanMessage" else "🤖 AI"
            print(f"{prefix}: {msg.content}")
        print("-" * 40)

    # 5. Print the Judge's Evaluation
    print("\n==========================================")
    print("            JUDGE'S EVALUATION            ")
    print("==========================================")
    print(f"Verdict     : {result.get('Judge_response')}")
    print(f"Reason      : {result.get('Judge_reason')}")
    print(f"Loops Taken : {result.get('max_loop')} out of your max_tries")
    print("==========================================\n")

if __name__ == "__main__":
    asyncio.run(run_full_workflow_test())