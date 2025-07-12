#!/usr/bin/env python
# chat_api.py – Saayam-for-All RAG chatbot
# Pinecone v3  +  Gemini 2.5 Flash  +  website fallback  +  conversational polish

"""
Install once
============
pip install fastapi uvicorn python-dotenv "pinecone>=3" \
            sentence-transformers google-generativeai requests \
            beautifulsoup4 numpy

.env (same folder, **no inline comments**)
=========================================
PINECONE_API_KEY=pcsk_...
PINECONE_ENV=us-east-1
PINECONE_INDEX=sayaam
GOOGLE_API_KEY=AIza...
GEMINI_MODEL=gemini-2.5-flash

Run
===
python -m uvicorn chat_api:app --reload --env-file .env
"""

# ───────────────────────── bootstrap env ──────────────────────────────
import os, re, numpy as np
from pathlib import Path
from typing import List

from dotenv import dotenv_values
env_file = Path(__file__).resolve().parent / ".env"
for k, v in dotenv_values(env_file).items():
    if v and k not in os.environ:
        os.environ[k] = v

# ───────────────────────── external libs ─────────────────────────────
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import google.generativeai as genai

# ───────────────────────── sanity check ──────────────────────────────
for req in ("PINECONE_API_KEY","PINECONE_ENV","PINECONE_INDEX","GOOGLE_API_KEY"):
    if not os.getenv(req):
        raise RuntimeError(f"Missing {req} in .env")

# ───────────────────────── config / clients ──────────────────────────
PC_API, PC_ENV, PC_IDX = os.environ["PINECONE_API_KEY"], os.environ["PINECONE_ENV"], os.environ["PINECONE_INDEX"]
GEM_API  = os.environ["GOOGLE_API_KEY"]
GEM_MODEL= os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

TOP_K      = int(os.getenv("TOP_K", 6))
EMB_MODEL  = "all-MiniLM-L6-v2"

embedder = SentenceTransformer(EMB_MODEL)
pc       = Pinecone(api_key=PC_API)
index    = pc.Index(PC_IDX)

genai.configure(api_key=GEM_API)
gemini = genai.GenerativeModel(GEM_MODEL)

# ───────────────────────── helpers ───────────────────────────────────
GREETINGS = {"hi","hello","hey","hii","good morning","good afternoon","good evening"}
def is_greeting(txt:str)->bool:
    t=txt.lower().strip()
    return any(t==g or t.startswith(g+" ") for g in GREETINGS)

# ---- simple website cache ------------------------------------------
_site:str|None=None
def site_text(url:str="https://saayamforall.org/")->str:
    global _site
    if _site: return _site
    html = requests.get(url,timeout=20).text
    soup = BeautifulSoup(html,"html.parser")
    for tag in soup(["script","style","noscript"]): tag.decompose()
    _site = re.sub(r"\s+"," ", soup.get_text(" ",strip=True))
    return _site

def site_ctx(question:str, thr:float=0.15)->list[str]:
    txt = site_text()
    if not txt: return []
    qv  = embedder.encode(question).tolist()
    tv  = embedder.encode([txt]).tolist()[0]
    sim = float(np.dot(qv,tv)/(np.linalg.norm(qv)*np.linalg.norm(tv)))
    return [txt[:2000]] if sim>thr else []

# ---- prompt builder -------------------------------------------------
SYSTEM_PROMPT = (
    "You’re Saayam-for-All’s friendly helper.  Be concise, upbeat, and speak in "
    "first-person plural (\"we\").  Base every answer on the CONTEXT.  If the "
    "answer isn’t there, say we’ll check with a volunteer."
)
def prompt(ctx:List[str], q:str, hist:List[str]|None)->str:
    conversation="\n".join(hist or [])
    return f"{SYSTEM_PROMPT}\n\nCONVERSATION:\n{conversation}\n\nCONTEXT:\n" + \
           "\n\n".join(ctx) + f"\n\nQUESTION:\n{q}"

# ───────────────────────── schema / app ──────────────────────────────
class ChatRequest(BaseModel):
    question:str
    history:List[str]|None=None          # last few user / bot turns

class ChatResponse(BaseModel):
    answer:str
    sources:List[str]

app = FastAPI(title="Saayam Gemini Chatbot")

# ───────────────────────── main route ────────────────────────────────
@app.post("/chat",response_model=ChatResponse)
def chat(req:ChatRequest):
    if is_greeting(req.question):
        return ChatResponse(answer="Hi! How can we help you with Saayam-for-All today?",
                            sources=[])

    try:
        # 1) retrieve
        q_vec = embedder.encode(req.question).tolist()
        res   = index.query(vector=q_vec, top_k=TOP_K, include_metadata=True)
        chunks=[str(m.metadata.get("text") or m.metadata.get("chunk") or "")
                for m in res.matches]
        paths =[m.metadata.get("path","") for m in res.matches]

        # 2) first Gemini call
        answer = gemini.generate_content(
            prompt(chunks, req.question, req.history),
            generation_config={"temperature":0.35}
        ).text.strip()

        # 3) live-site fallback
        if answer.lower().startswith(("i don’t know","i don't know")):
            ctx2 = site_ctx(req.question)
            if ctx2:
                answer = gemini.generate_content(
                    prompt(ctx2, req.question, req.history),
                    generation_config={"temperature":0.35}
                ).text.strip()
                if not answer.lower().startswith(("i don’t know","i don't know")):
                    paths.append("https://saayamforall.org/")

        # 4) final snippet fallback
        if answer.lower().startswith(("i don’t know","i don't know")) and (chunks or ctx2):
            snippet=(chunks or ctx2)[0].strip().replace("\n"," ")[:300]
            answer = f"I’m not completely sure, but here’s something we found:\n\n{snippet}"

        # 5) polish
        answer = answer.replace("* ", "• ")
        if answer.lower().startswith("saayam-for-all can help"):
            answer = answer.replace("Saayam-for-All can help you",
                                    "Sure — we can help you")

        # dedupe sources
        seen,uniq=set(),[]
        for p in paths:
            if p and p not in seen:
                uniq.append(p); seen.add(p)

        return ChatResponse(answer=answer, sources=uniq)

    except Exception as e:
        import traceback; traceback.print_exc()
        from fastapi.responses import JSONResponse
        from fastapi import status
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={"error":str(e)})
