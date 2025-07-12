from fastapi import FastAPI
from pydantic import BaseModel
from saayam_rag.chain import rag_chain, memory
from saayam_rag.website_fallback import maybe_context
from typing import List

GREETINGS={"hi","hello","hey","hii","good morning","good afternoon","good evening"}

class Req(BaseModel):
    question:str

class Resp(BaseModel):
    answer:str
    sources:List[str]

app=FastAPI(title="Saayam RAG API")

def greet(q:str)->bool:
    t=q.lower().strip()
    return any(t==g or t.startswith(g+" ") for g in GREETINGS)

@app.post("/chat",response_model=Resp)
def chat(req:Req):
    if greet(req.question):
        memory.clear()
        return Resp(answer="Hi! How can we help you with Saayam-for-All today?",
                    sources=[])

    result = rag_chain(req.question)
    answer = result["answer"]
    srcs   = [d.metadata.get("path","") for d in result["source_documents"]]

    if answer.lower().startswith(("i don’t know","i don't know")):
        ctx = maybe_context(req.question)
        if ctx:
            answer = rag_chain.combine_docs_chain.llm_chain.predict(
                question=req.question, context=ctx)
            if not answer.lower().startswith(("i don’t know","i don't know")):
                srcs.append("https://saayamforall.org/")

    answer = answer.replace("* ","• ")
    if answer.lower().startswith("saayam-for-all can help"):
        answer = answer.replace("Saayam-for-All can help you","Sure — we can help you")

    # dedupe
    seen,uniq=set(),[]
    for s in srcs:
        if s and s not in seen:
            uniq.append(s); seen.add(s)

    return Resp(answer=answer, sources=uniq)
