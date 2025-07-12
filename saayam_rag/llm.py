# saayam_rag/llm.py
from langchain_google_genai import ChatGoogleGenerativeAI
from .config import GEM_KEY, GEM_MODEL

llm = ChatGoogleGenerativeAI(
    google_api_key = GEM_KEY,
    model          = GEM_MODEL,
    temperature    = 0.35,
    convert_system_message_to_human = True,   # let LC treat system as human msg
)
