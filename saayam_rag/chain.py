from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from .vector_store import retriever
from .llm import llm

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="answer",          # ← store only the final text, not docs
)

SYSTEM_PROMPT = (
    "You’re Saayam-for-All’s friendly helper. Be concise, upbeat, "
    "and speak in first-person plural ('we'). Base answers ONLY on the context. "
    "If the answer isn’t there, say we’ll check with a volunteer."
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("system", "Context:\n{context}"),
        ("human", "{question}"),
    ]
)

rag_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    memory=memory,
    verbose=False,
    return_source_documents=True,                 # ← ADD THIS
    combine_docs_chain_kwargs={
        "prompt": prompt,
        "document_variable_name": "context",
    },
)
