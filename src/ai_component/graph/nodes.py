import os
import sys
from src.utils import utils
from src.ai_component.llm import LLMClient
from src.ai_component.core.models import Check
from src.ai_component.graph.state import GraphState
from src.ai_component.tools.web_tool import web_tool
from src.ai_component.tools.rag_tool import pdf_search_tool
from src.ai_component.core.prompts import system_prompt, judge_system_prompt
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
            
    async def LLMJudgeNode(self, state: GraphState) -> dict:
        try:
            messages = state.get('messages', [])
            current_loops = state.get('max_loop', 0) +1

            if not messages:
                return {"Judge_response": "No", "Judge_reason": "No messages found.", "max_loop": current_loops}

            query = next((msg.content for msg in messages if isinstance(msg, HumanMessage)), "")
            response_text = messages[-1].content if isinstance(messages[-1], AIMessage) else ""

            if not response_text.strip():
                return {"Judge_response": "No", "Judge_reason": "Empty response.", "max_loop": current_loops}

            prompt = ChatPromptTemplate.from_messages([("system", judge_system_prompt)])
            variables = {"query": query.strip(), "response": response_text.strip()}

            result = await self.client.invoke_structured(Check, prompt, variables)
            
            state_update = {
                "Judge_response": result.verdict,
                "Judge_reason": result.reason,
                "max_loop": current_loops
            }
            
            if result.verdict == "No" and current_loops < utils.max_tries: 
                feedback = HumanMessage(
                    content=f"System Feedback: Your previous answer was rejected. Reason: {result.reason}. Please modify your answer to align with the documents and try again."
                )
                state_update["messages"] = [feedback]

            return state_update

        except Exception as e:
            logging.error(f"Error in LLMJudge Node: {str(e)}")
            raise CustomException(e, sys) from e