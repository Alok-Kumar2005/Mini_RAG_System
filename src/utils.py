import os
from dotenv import load_dotenv

load_dotenv()



class Utils:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

    max_tries: int = 3


utils = Utils()