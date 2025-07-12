# saayam_rag/vector_store.py
from langchain_pinecone import PineconeVectorStore      # ← NEW import
from .config import pc, PC_IDX, embedder

# wrap the v3 index
vectorstore = PineconeVectorStore(
    index          = pc.Index(PC_IDX),   # existing index handle
    embedding      = embedder,           # keyword is `embedding`
    text_key       = "text",
    namespace      = "",                 # default
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
