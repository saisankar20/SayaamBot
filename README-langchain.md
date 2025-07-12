# Saayam‑bot Repository Docs Bundle

Below are the five text resources you asked for — ready to copy or split into separate files as you commit.

---

## 1. `.gitignore`

```
# ── Python artefacts
__pycache__/
*.py[cod]
*.egg-info/

# ── Virtual‑envs
.venv/
venv/
env/

# ── IDE / OS noise
.vscode/
.idea/
.DS_Store

# ── Secrets
.env
.env.*

# but keep the public template
!.env.template
```

---

## 2. `.env.template`

```
# Copy to .env and paste real keys
PINECONE_API_KEY=
PINECONE_ENV=us-east-1
PINECONE_INDEX=sayaam
GOOGLE_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
```

---

## 3. `README.md`  *(root ‑ present on **both** branches)*

````markdown
# Saayam-for-All Chatbot

This repository hosts two flavours of a Retrieval‑Augmented Generation (RAG)
chatbot that answers questions about Saayam‑for‑All.

| Branch | Tech stack | Highlights | Entry‑point |
|--------|-----------|------------|-------------|
| **main** | Classic Python | Single‑file FastAPI, direct Pinecone, Gemini 2.5 | `chat_api.py` |
| **langchain** | LangChain 0.2 | Modular folders, ConversationalRetrievalChain, live‑site fallback | `api/` |

```bash
# clone & choose
git clone https://github.com/<you>/saayam-bot.git
cd saayam-bot
git switch langchain   # or: git switch main
````

Each branch carries its own README with detailed setup.

````

---

## 4. `README-classic.md`  *(commit on **main** branch)*
```markdown
# Saayam Chatbot – Classic Version

A minimal Retrieval‑Augmented chatbot without LangChain.

## Features
* FastAPI endpoint `/chat`
* Sentence‑Transformers embeddings (`all-MiniLM-L6-v2`)
* Pinecone v3 vector DB
* Google Gemini 2.5 Flash completion
* Optional live‑site fallback (scrapes https://saayamforall.org)

## Quick‑start
```bash
python -m venv .venv && source .venv/bin/activate          # Win: .\.venv\Scripts\activate
pip install -r requirements.txt
cp .env.template .env    # add keys

# embed the PDF
python index_code.py --root SaayamForAll.pdf

# run API
python -m uvicorn chat_api:app --reload --env-file .env

# terminal chat
python chat_cli.py
````

````

---

## 5. `README-langchain.md`  *(commit on **langchain** branch)*
```markdown
# Saayam Chatbot – **LangChain** Edition

Modular ConversationalRetrievalChain powered by Gemini 2.5 Flash & Pinecone.

## Project layout
```text
saayam-bot/
├─ ingest/ingest_pdf.py
├─ saayam_rag/
│   ├─ config.py
│   ├─ vector_store.py
│   ├─ website_fallback.py
│   ├─ llm.py
│   └─ chain.py
└─ api/
    ├─ server.py
    └─ cli.py
````

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
cp .env.template .env    # add API keys
```

### Ingest docs

```bash
python ingest/ingest_pdf.py --root SaayamForAll.pdf
```

### Run API

```bash
python -m uvicorn api.server:app --reload --env-file .env
```

### Chat

```bash
python api/cli.py
```

## Key features

* ConversationalRetrievalChain with history
* Friendly "we" tone via custom system prompt
* Website fallback when Pinecone lacks answer
* Secrets kept out of Git via `.env.template`

```
```
