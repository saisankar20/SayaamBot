#!/usr/bin/env python
# api/server.py – FastAPI endpoint that wraps the LangChain RAG chain
# Adds CORS so the Vite front-end (http://localhost:5173) can call /chat.

from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware            # ← NEW
from pydantic import BaseModel

from saayam_rag.chain import rag_chain, memory
from saayam_rag.website_fallback import maybe_context

# ─────────────────────────────── config ──────────────────────────────
GREETINGS = {
    "hi", "hello", "hey", "hii", "good morning",
    "good afternoon", "good evening",
}

# change this if your front-end runs elsewhere
FRONTEND_ORIGIN = "http://localhost:5173"

# ─────────────────────────── data models ─────────────────────────────
class Req(BaseModel):
    question: str

class Resp(BaseModel):
    answer: str
    sources: List[str]

# ───────────────────────────── FastAPI ───────────────────────────────
app = FastAPI(title="Saayam RAG API")

# ---- enable CORS so the browser can reach the API -------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────── helpers ─────────────────────────────────
def greet(q: str) -> bool:
    t = q.lower().strip()
    return any(t == g or t.startswith(g + " ") for g in GREETINGS)

# ─────────────────────────── routes ──────────────────────────────────
@app.post("/chat", response_model=Resp)
def chat(req: Req):
    # reset convo on greeting
    if greet(req.question):
        memory.clear()
        return Resp(
            answer="Hi! How can we help you with Saayam-for-All today?",
            sources=[],
        )

    # 1) run LangChain RAG
    result = rag_chain.invoke({"question": req.question})
    answer: str = result["answer"]
    srcs = [d.metadata.get("path", "") for d in result["source_documents"]]

    # 2) website fallback
    if answer.lower().startswith(("i don’t know", "i don't know")):
        ctx = maybe_context(req.question)
        if ctx:
            answer = rag_chain.combine_docs_chain.llm_chain.predict(
                question=req.question,
                context=ctx,
            )
            if not answer.lower().startswith(("i don’t know", "i don't know")):
                srcs.append("https://saayamforall.org/")

    # 3) style tweaks
    answer = answer.replace("* ", "• ")
    if answer.lower().startswith("saayam-for-all can help"):
        answer = answer.replace(
            "Saayam-for-All can help you", "Sure — we can help you"
        )

    # 4) dedupe sources
    seen, uniq = set(), []
    for s in srcs:
        if s and s not in seen:
            uniq.append(s)
            seen.add(s)

    return Resp(answer=answer, sources=uniq)
