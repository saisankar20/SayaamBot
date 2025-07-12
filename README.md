# Saayam-for-All Chatbot

This repository contains two flavours of a Retrieval-Augmented Generation
(RAG) chatbot that answers questions about the Saayam-for-All NGO.

| Branch | Tech stack | Highlights | Entry-point |
|--------|------------|------------|-------------|
| **main** | Classic Python | Single-file FastAPI, direct Pinecone, Gemini 2.5 | `chat_api.py` |
| **langchain** | LangChain 0.2 | Modular folders, ConversationalRetrievalChain, live-site fallback | `api/` |

```bash
# clone & choose a version
git clone https://github.com/<you>/saayam-bot.git
cd saayam-bot
git switch langchain   # or: git switch main
