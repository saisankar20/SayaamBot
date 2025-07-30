# saayam_rag/chain.py
"""
Builds a Conversational RAG chain with:
• Pinecone retriever
• Google-Gemini LLM
• ConversationBufferMemory to preserve chat history
The system prompt is tuned for a friendly, clarifying assistant.
"""

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from .vector_store import retriever
from .llm import llm

# ─────────────────────────── memory ────────────────────────────────
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="answer",          # store only final text (not docs) in memory
)

# ───────────────────────── system prompt ────────────────────────────
SYSTEM_PROMPT = (
    "You're Saayam-for-All’s helpful assistant. "
    "Speak clearly, warmly, and conversationally—as if you're chatting with a friend. "
    "Use 'we' when offering help on behalf of the organisation. "
    "Base answers **only** on the context provided; never invent facts. "
    "If you're unsure, kindly ask the user to clarify. "
    "Keep responses concise and avoid repeating yourself."
)

# ───────────────────────── prompt template ──────────────────────────
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("system", "Context:\n{context}"),
        ("human", "{question}"),
    ]
)

# ───────────────────── Conversational RAG chain ─────────────────────
rag_chain: ConversationalRetrievalChain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    memory=memory,
    verbose=False,
    return_source_documents=True,
    combine_docs_chain_kwargs={
        "prompt": prompt,
        "document_variable_name": "context",
    },
)
