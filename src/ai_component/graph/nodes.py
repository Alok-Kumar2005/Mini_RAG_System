import os
import sys
from src.utils import utils
from src.ai_component.llm import LLMClient
from src.ai_component.core.models import Check
from src.ai_component.graph.state import GraphState
from src.ai_component.tools.web_tool import web_tool
from src.ai_component.tools.rag_tool import pdf_search_tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from src.ai_component.core.prompts import system_prompt, judge_system_prompt, summarizer_prompt1, summarizer_prompt2
from langchain_core.messages.utils import trim_messages, count_tokens_approximately
from langchain.messages import RemoveMessage

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
            
            session_id = state.get("session_id", "")
            
            # Dynamic system prompt based on whether a PDF is loaded
            if session_id:
                dynamic_prompt = system_prompt + f"\n\nA document is currently loaded (session: active). You MUST use search_pdf_tool to answer any document-related questions. Do NOT answer from memory."
            else:
                dynamic_prompt = system_prompt + "\n\nNo document is currently uploaded. Inform the user they need to upload a PDF first if they ask document questions."

            messages_for_trim = []
            summary = state.get("summarize", "")
            if summary:
                messages_for_trim.append({
                    "role": "system",
                    "content": summary,
                })
            messages_for_trim.extend(state['messages'])
            
            trimmed = trim_messages(
                messages=messages_for_trim,
                strategy="last",
                token_counter=count_tokens_approximately,
                max_tokens=utils.MAX_CONTEXT,
            )
                
            template = ChatPromptTemplate.from_messages([
                ("system", dynamic_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
            ])
            result = await self.client.invoke_tool(
                tools=tools,
                prompt=template,
                variables={"chat_history": trimmed},
            )
            return {
                "messages": [result],
                "session_id": session_id,
            }

        except Exception as e:
            logging.error(f"Error in Query Node: {str(e)}")
            raise CustomException(e, sys) from e
            
    async def LLMJudgeNode(self, state: GraphState) -> dict:
        try:
            messages = state.get("messages", [])
            current_loops = state.get("max_loop", 0) + 1

            if not messages:
                return {"Judge_response": "No", "Judge_reason": "No messages found.", "max_loop": current_loops}

            # Get the LAST human message, not the first
            query = ""
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage) and not msg.content.startswith("System Feedback:"):
                    query = msg.content
                    break

            response_text = messages[-1].content if isinstance(messages[-1], AIMessage) else ""

            if not response_text.strip():
                return {"Judge_response": "No", "Judge_reason": "Empty response.", "max_loop": current_loops}

            prompt = ChatPromptTemplate.from_messages([("system", judge_system_prompt)])
            variables = {"query": query.strip(), "response": response_text.strip()}

            result = await self.client.invoke_structured(Check, prompt, variables)

            state_update = {
                "Judge_response": result.verdict,
                "Judge_reason": result.reason,
                "max_loop": current_loops,
                "session_id": state.get("session_id", ""),
            }

            if result.verdict == "No" and current_loops < utils.max_tries:
                feedback = HumanMessage(
                    content=(
                        f"System Feedback: Your previous answer was rejected. "
                        f"Reason: {result.reason}. "
                        f"Please modify your answer to align with the documents and try again."
                    )
                )
                state_update["messages"] = [feedback]

            return state_update

        except Exception as e:
            logging.error(f"Error in LLMJudge Node: {str(e)}")
            raise CustomException(e, sys) from e
        
    async def summarizer(self, state: GraphState) -> dict:
        try:
            existing_summary = state.get("summarize", "")
            messages = state.get("messages", [])

            if existing_summary:
                template = ChatPromptTemplate.from_messages([("system", summarizer_prompt1)])
            else:
                template = ChatPromptTemplate.from_messages([("system", summarizer_prompt2)])

            variables = {"existing_conversation": messages}
            summary: str = await self.client.invoke_with_template(template, variables)

            keep = max(utils.MAX_CONVERSATION // 2, 4)
            messages_to_delete = messages[:-keep] if len(messages) > keep else []

            return {
                "messages": [RemoveMessage(id=m.id) for m in messages_to_delete],
                "summarize": summary,
            }

        except Exception as e:
            logging.error(f"Error in Summarizer node: {str(e)}")
            raise CustomException(e, sys) from e