from pydantic import BaseModel, Field
from typing import Literal


from pydantic import BaseModel, Field
from typing import Literal

class Check(BaseModel):
    verdict: Literal['Yes', 'No'] = Field(
        ...,
        description="Whether the LLM response correctly answers the user query."
    )
    reason: str = Field(
        ...,
        description="Short explanation for the verdict."
    )