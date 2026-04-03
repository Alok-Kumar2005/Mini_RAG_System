import os
import sys
from src.ai_component.llm import LLMClient
from src.ai_component.graph.state import GraphState
from src.ai_component.tools.web_tool import web_tool
from src.ai_component.core.prompts import system_prompt
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from src.logger import logging
from src.exceptions import CustomException

tools = [web_tool]

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
                variables={"chat_history": messages}
            )
            return {"messages": [result]}
                    
        except Exception as e:
            logging.error(f"Error in Query Node: {str(e)}")
            raise CustomException(e, sys) from e
            
