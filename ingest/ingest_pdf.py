#!/usr/bin/env python
"""Extract text (PDF & text files) and upsert to Pinecone v3."""
import os, argparse, hashlib
from pathlib import Path
from typing import List

import dotenv
from pypdf import PdfReader
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec

dotenv.load_dotenv()

def iter_files(root: Path, exts: List[str]):
    for p in root.rglob("*"):
        if p.suffix.lower() in exts and p.is_file():
            yield p

def chunk(txt:str,mx=4000,ov=200):
    for i in range(0,len(txt),mx-ov):
        yield txt[i:i+mx]

sha1 = lambda s: hashlib.sha1(s.encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",required=True)
    ap.add_argument("--index",default=os.getenv("PINECONE_INDEX","sayaam"))
    args=ap.parse_args()

    pc  = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    if args.index not in pc.list_indexes().names():
        pc.create_index(args.index,dimension=384,metric="cosine",
                        spec=ServerlessSpec(cloud="aws",
                                            region=os.environ["PINECONE_ENV"]))
    index = pc.Index(args.index)
    embed = SentenceTransformer("all-MiniLM-L6-v2")

    root  = Path(args.root)
    exts  = {".pdf",".md",".txt",".py",".js",".java",".cpp",".rs",".go"}
    files = [root] if root.is_file() else list(iter_files(root,exts))
    ids,txts,meta=[],[],[]
    for fp in tqdm(files):
        if fp.suffix.lower()==".pdf":
            txt="\n".join(p.extract_text() or "" for p in PdfReader(fp).pages)
        else:
            txt=fp.read_text(encoding="utf-8",errors="ignore")
        for i,chunk in enumerate(chunk(txt)):
            ids.append(sha1(f"{fp}:{i}"))
            txts.append(chunk)
            meta.append({"path":str(fp),"chunk":i,"text":chunk})
            if len(ids)>=32:
                flush(index,embed,ids,txts,meta); ids,txts,meta=[],[],[]
    if ids: flush(index,embed,ids,txts,meta)
    print("✅ Ingest done.")

def flush(index,embed,ids,txts,meta):
    vecs=embed.encode(txts).tolist()
    index.upsert([{"id":i,"values":v,"metadata":m}
                  for i,v,m in zip(ids,vecs,meta)])

if __name__=="__main__":
    main()
