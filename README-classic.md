# Saayam Chatbot – Classic Version

A minimal Retrieval-Augmented chatbot without LangChain.

## Features
* FastAPI endpoint **`/chat`**
* Sentence-Transformers embeddings (`all-MiniLM-L6-v2`)
* Pinecone v3 vector DB
* Google Gemini 2.5 Flash completion
* Optional live-site fallback (scrapes <https://saayamforall.org>)

## Quick-start

```bash
python -m venv .venv && source .venv/bin/activate       # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
cp .env.template .env    # paste your API keys

# 1) Embed docs into Pinecone
python index_code.py --root SaayamForAll.pdf

# 2) Run the API
python -m uvicorn chat_api:app --reload --env-file .env

# 3) Terminal chat
python chat_cli.py
