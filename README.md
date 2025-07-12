# Saayam-for-All Chatbot

This repository hosts two flavours of a Retrieval-Augmented Generation chatbot
that answers questions about Saayam-for-All – a volunteer-driven NGO.

| Branch | Tech stack | Highlights | Entry-point |
| ------ | ---------- | ---------- | ----------- |
| **main** | Classic Python | Single-file FastAPI, direct Pinecone, Gemini 2.5 | `chat_api.py` |
| **langchain** | LangChain 0.2 | Modular folders, ConversationalRetrievalChain, live-website fallback | `api/` |

```bash
git clone https://github.com/<you>/saayam-bot.git
cd saayam-bot
git switch langchain   # or: git switch main
