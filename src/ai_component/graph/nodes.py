import os
import sys
from src.ai_component.llm import LLMClient
from src.ai_component.graph.state import GraphState
from src.ai_component.tools.web_tool import web_tool
from src.ai_component.tools.rag_tool import pdf_search_tool
from src.ai_component.core.prompts import system_prompt
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from src.logger import logging
from src.exceptions import CustomException

tools = [web_tool, pdf_search_tool]

class Nodes:
    def __init__(self):
        self.client = LLMClient()

    async def QueryNode(self, state: GraphState) -> dict:
        try:
            messages = state.get("messages", [])
            if not messages:
                return {"messages": []}
                
            template = ChatPromptTemplate.from_messages([
                ('system', system_prompt),
                MessagesPlaceholder(variable_name="chat_history")
            ])
            result = await self.client.invoke_tool(
                tools=tools, 
                prompt=template, 
                variables={"chat_history": state["messages"]}
            )
            return {"messages": [result]}
                    
        except Exception as e:
            logging.error(f"Error in Query Node: {str(e)}")
            raise CustomException(e, sys) from e
            
import asyncio
async def run_test():
    # You'll need your tool imported here for the manual test simulation
    from src.ai_component.tools.rag_tool import pdf_search_tool
    
    nodes = Nodes()
    
    # 1. Create a mock state representing a user who just uploaded "doc_123"
    print("--- 1. Setting up the State ---")
    test_state = {
        "messages": [HumanMessage(content="What does the document say about architecture?")],
        "session_id": "doc_user_aveek_123"
    }
    print(f"User Query: {test_state['messages'][0].content}")
    print(f"Active Session ID: {test_state['session_id']}\n")

    # 2. Run the Node
    print("--- 2. Running QueryNode (The Brain) ---")
    update = await nodes.QueryNode(test_state)
    result_msg = update["messages"][0]
    
    # 3. Check what the LLM decided to do
    if result_msg.tool_calls:
        tool_call = result_msg.tool_calls[0]
        print("✅ SUCCESS: The LLM recognized it needs to search the PDF!")
        print(f"Tool to execute: {tool_call['name']}")
        print(f"LLM Generated Query: {tool_call['args']['query']}\n")
        
        # 4. SIMULATING THE TOOL NODE EXECUTION
        # Because we aren't using the LangGraph StateGraph yet, we have to 
        # manually pass the state into the tool to prove the InjectedState works.
        print("--- 3. Simulating Tool Execution ---")
        
        # We manually pass the test_state here. 
        # In the real app, LangGraph's ToolNode does this step automatically.
        tool_result = await pdf_search_tool._arun(
            query=tool_call["args"]["query"],
            state=test_state 
        )
        print(f"Tool Output:\n{tool_result}")
        
    else:
        print("❌ FAIL: The LLM just answered directly.")
        print(f"Response: {result_msg.content}")

if __name__ == "__main__":
    asyncio.run(run_test())