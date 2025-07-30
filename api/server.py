#!/usr/bin/env python

import sys
import os
import re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from saayam_rag.chain import rag_chain, memory
from saayam_rag.website_fallback import maybe_context

# ─────────────────────────────── config ──────────────────────────────
GREETINGS = {
    "hi", "hello", "hey", "hii", "good morning",
    "good afternoon", "good evening",
}

FRONTEND_ORIGIN = "http://localhost:5173"

# Store temporary state in memory (per session basis)
follow_up_state = {
    "asked_clarification": False,
    "asked_for_contact": False,
    "volunteer_requested": False,
}

# ─────────────────────────── data models ─────────────────────────────
class Req(BaseModel):
    question: str

class Resp(BaseModel):
    answer: str
    sources: List[str]

# ───────────────────────────── FastAPI ───────────────────────────────
app = FastAPI(title="Saayam RAG API")

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

def is_affirmative(text: str) -> bool:
    return text.lower().strip() in {"yes", "yeah", "yep", "sure", "please", "ok"}

def is_phone_number(text: str) -> bool:
    return bool(re.match(r"^[\d\s()+-]{7,}$", text.strip()))

# ─────────────────────────── routes ──────────────────────────────────
@app.post("/chat", response_model=Resp)
def chat(req: Req):
    q = req.question.strip()

    # Handle greetings
    if greet(q):
        memory.clear()
        follow_up_state.update({
            "asked_clarification": False,
            "asked_for_contact": False,
            "volunteer_requested": False,
        })
        return Resp(answer="Hey there! 👋 How can we help you with Saayam-for-All today?", sources=[])

    # Handle empty input
    if not q:
        return Resp(answer="Oops, looks like your message is empty. Could you try asking your question again?", sources=[])

    # Follow-up: got phone number after volunteer connect
    if follow_up_state["asked_for_contact"] and is_phone_number(q):
        follow_up_state["asked_for_contact"] = False
        follow_up_state["volunteer_requested"] = False
        return Resp(answer="Thanks! We’re connecting you with a volunteer now. You’ll hear from us soon. 📞", sources=[])

    # Follow-up: user said yes to volunteer help
    if follow_up_state["asked_clarification"] and is_affirmative(q):
        follow_up_state["asked_clarification"] = False
        follow_up_state["asked_for_contact"] = True
        return Resp(answer="Sure! Could you please share your phone number so we can reach out?", sources=[])

    # 1. Try to answer using RAG
    result = rag_chain.invoke({"question": q})
    answer: str = result["answer"]
    srcs = ["a trusted source" for _ in result["source_documents"] if _]

    # 2. If answer is unknown, try fallback website context
    if answer.lower().startswith(("i don’t know", "i don't know")):
        ctx = maybe_context(q)
        if ctx:
            answer = rag_chain.combine_docs_chain.llm_chain.predict(
                question=q,
                context=ctx,
            )
            if not answer.lower().startswith(("i don’t know", "i don't know")):
                srcs.append("https://saayamforall.org/")

    # 3. Still doesn't know — enter clarification flow
    if answer.lower().startswith(("i don’t know", "i don't know")):
        if not follow_up_state["asked_clarification"]:
            follow_up_state["asked_clarification"] = True
            return Resp(
                answer="Hmm, I’m not quite sure I understood that. Could you explain it another way?",
                sources=[],
            )
        else:
            follow_up_state["asked_clarification"] = False
            follow_up_state["asked_for_contact"] = True
            return Resp(
                answer="Would you like me to connect you with a volunteer?",
                sources=[],
            )

    # 4. Friendly answer formatting
    answer = answer.replace("* ", "👉 ")
    answer = re.sub(
        r"\b(Saayam-for-All|this system|this application) can help you\b",
        "Sure — we can help you",
        answer,
        flags=re.IGNORECASE
    )

    # 5. Deduplicate sources
    seen, uniq = set(), []
    for s in srcs:
        if s and s not in seen:
            uniq.append(s)
            seen.add(s)

    return Resp(answer=answer.strip(), sources=uniq)
