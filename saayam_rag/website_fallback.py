import re, numpy as np, requests, bs4, sentence_transformers
from .config import embedder

_cache:str|None=None
def text():
    global _cache
    if _cache: return _cache
    html=requests.get("https://saayamforall.org/",timeout=20).text
    soup=bs4.BeautifulSoup(html,"html.parser")
    for t in soup(["script","style","noscript"]): t.decompose()
    _cache=re.sub(r"\s+"," ",soup.get_text(" ",strip=True))
    return _cache

hf = sentence_transformers.SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

def maybe_context(q:str,thr=0.15):
    t=text()
    qv,hv = hf.encode(q,normalize_embeddings=True), hf.encode(t,normalize_embeddings=True)
    if np.dot(qv,hv) > thr: return t[:2000]
    return None
