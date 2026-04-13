import os
from dotenv import load_dotenv

load_dotenv()



class Utils:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

    max_tries: int = 2

    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    # EMBEDDING_DIM = 384
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60*24

    MAX_CONTEXT: int = 1500
    MAX_CONVERSATION: int = 30

    DATABASE_URL = os.getenv("DATABASE_URL")
    DIRECT_DATABASE_URL = os.getenv("DIRECT_DATABASE_URL")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-2-preview")
    GEMINI_OUTPUT_DIMS = os.getenv("GEMINI_OUTPUT_DIMS", 768)

utils = Utils()