from __future__ import annotations
import sys
from typing import Any, Type, Optional, Dict, Union
from pydantic import BaseModel

from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

from src.logger import logging
from src.exceptions import CustomException
from src.utils import utils

class LLMClient:
    def __init__(self, temperature: float = 0.0, max_tokens: int = 4096, max_retries: int = 2):
        self.api_key = utils.GROQ_API_KEY
        self.model_name = utils.GROQ_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.llm = ChatGroq(
            model=self.model_name,
            api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            max_retries=self.max_retries
        )

    async def invoke(self, prompt: str) -> str:
        try:
            logging.info("Calling LLM with simple prompt.")
            response = await self.llm.ainvoke(prompt)
            return response.content
        except Exception as e:
            logging.error(f"Error in simple invocation: {str(e)}")
            raise CustomException(e, sys) from e

    async def invoke_with_template(self, prompt_template: ChatPromptTemplate, variables: Dict[str, Any]) -> str:
        try:
            logging.info("Calling LLM with prompt template.")
            chain = prompt_template | self.llm
            response = await chain.ainvoke(variables)
            return response.content
        except Exception as e:
            logging.error(f"Error in template invocation: {str(e)}")
            raise CustomException(e, sys) from e

    async def invoke_structured(
        self, 
        schema: Type[BaseModel], 
        prompt: Union[str, ChatPromptTemplate, PromptTemplate], 
        variables: Optional[Dict[str, Any]] = None
    ) -> BaseModel:
        try:
            logging.info(f"Calling structured LLM for schema: {schema.__name__}")
            structured_llm = self.llm.with_structured_output(schema)
            
            if isinstance(prompt, (ChatPromptTemplate, PromptTemplate)):
                chain = prompt | structured_llm
                response = await chain.ainvoke(variables or {})
            else:
                response = await structured_llm.ainvoke(prompt)
                
            return response
        except Exception as e:
            logging.error(f"Error in structured invocation: {str(e)}")
            raise CustomException(e, sys) from e
        
    async def invoke_tool(
            self, tools: list,
            prompt: Union[str, ChatPromptTemplate, PromptTemplate],
            variables: Optional[Dict[str, Any]] = None
    )-> BaseMessage:
        try:
            logging.info(f"Calling LLM with tools: {tools}")
            tool_llm = self.llm.bind_tools(tools)

            if isinstance(prompt, (ChatPromptTemplate, PromptTemplate)):
                chain = prompt | tool_llm
                response = await chain.ainvoke(variables or {})
            else:
                response = await tool_llm.ainvoke(prompt)
                
            return response
        except Exception as e:
            logging.error(f"Error in tool LLM: {str(e)}")
            raise CustomException(e, sys) from e
        

import asyncio
from pydantic import BaseModel, Field
class UserProfile(BaseModel):
    name: str = Field(description="The name of the user")
    age: int = Field(description="The age of the user")
    hobbies: list[str] = Field(description="List of hobbies")

async def main():
    client = LLMClient(temperature=0.2)
    print("--- Scenario 1: Simple ---")
    simple_result = await client.invoke("What is the capital of Japan?")
    print(simple_result)

    print("\n--- Scenario 2: Template ---")
    template = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful travel guide."),
        ("human", "Give me {count} tourist spots in {city}.")
    ])
    template_result = await client.invoke_with_template(
        prompt_template=template, 
        variables={"count": 3, "city": "Paris"}
    )
    print(template_result)

    print("\n--- Scenario 3: Structured Output ---")
    structured_str_result = await client.invoke_structured(
        schema=UserProfile,
        prompt="My name is John, I am 28 years old and I love reading and hiking."
    )
    print(f"Name: {structured_str_result.name}, Hobbies: {structured_str_result.hobbies}")

    structured_template = ChatPromptTemplate.from_template(
        "Extract the user profile from this text: {text}"
    )
    structured_tpl_result = await client.invoke_structured(
        schema=UserProfile,
        prompt=structured_template,
        variables={"text": "Sarah is a 32-year-old software engineer who enjoys painting."}
    )
    print(f"Name: {structured_tpl_result.name}, Age: {structured_tpl_result.age}")

if __name__ == "__main__":
    asyncio.run(main())