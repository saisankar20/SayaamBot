# saayam_rag/config.py
import os, dotenv
from pinecone import Pinecone
from langchain_community.embeddings import HuggingFaceEmbeddings
dotenv.load_dotenv()

# ─── env keys ───────────────────────────────────────────
PC_API   = os.environ["PINECONE_API_KEY"]
PC_ENV   = os.environ["PINECONE_ENV"]
PC_IDX   = os.environ["PINECONE_INDEX"]
GEM_KEY  = os.environ["GOOGLE_API_KEY"]
GEM_MODEL= os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ─── embeddings (implements embed_query / embed_documents) ───────────
embedder = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}          # change to "cuda" if GPU available
)

# ─── Pinecone client ─────────────────────────────────────────────────
pc = Pinecone(api_key=PC_API)
