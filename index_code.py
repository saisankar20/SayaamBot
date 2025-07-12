#!/usr/bin/env python
# index_code.py – Pinecone v3 ingestor (PDF-aware, .env-aware)

"""
First-time setup
----------------
    pip install python-dotenv sentence-transformers "pinecone>=3" tqdm
    # for PDFs:
    pip install pypdf

Typical runs
------------
    python index_code.py --root SaayamForAll.pdf          # uses .env defaults
    python index_code.py --root ./docs --index sayaam-dev
"""

import os, argparse, hashlib
from pathlib import Path
from typing import List

from dotenv import load_dotenv ; load_dotenv()
from tqdm import tqdm
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

# try pypdf; keep script usable if missing
try:
    from pypdf import PdfReader
except ModuleNotFoundError:
    PdfReader = None

# ───────── helpers ────────────────────────────────────────────────────
def iter_files(root: Path, exts: List[str]):
    for p in root.rglob("*"):
        if p.suffix.lower() in exts and p.is_file():
            yield p

def chunk_text(txt: str, max_chars=4000, overlap=200):
    start = 0
    while start < len(txt):
        end = min(start + max_chars, len(txt))
        yield txt[start:end]
        start += max_chars - overlap

sha1 = lambda t: hashlib.sha1(t.encode()).hexdigest()

# ───────── main ───────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser("Embed file/folder and upsert to Pinecone")
    ap.add_argument("--root",  help="file or directory to ingest")
    ap.add_argument("--index", default=os.getenv("PINECONE_INDEX", ""),
                    help="Pinecone index name (created if missing)")
    ap.add_argument("--model", default="all-MiniLM-L6-v2")
    ap.add_argument("--dim",   type=int, default=384)
    ap.add_argument("--batch", type=int,
                    default=int(os.getenv("EMBED_BATCH_SIZE", 32)))
    ap.add_argument("--api-key", default=os.getenv("PINECONE_API_KEY", ""))
    ap.add_argument("--env",     default=os.getenv("PINECONE_ENV", ""))
    args = ap.parse_args()

    # interactive fallbacks
    if not args.root:
        args.root = input("Path to file or directory to ingest: ").strip()
    if not args.index:
        args.index = input("Pinecone index name: ").strip()
    if not args.api_key:
        args.api_key = input("Pinecone API key: ").strip()
    if not args.env:
        args.env = input("Pinecone region (e.g. us-east-1): ").strip()

    region = args.env.replace("-aws", "")

    # collect files
    root_path = Path(args.root.strip('"').strip("'"))
    exts = {".py",".js",".ts",".tsx",".java",".cpp",".c",".cs",
            ".go",".rb",".php",".rs",".md",".pdf"}
    files = [root_path] if root_path.is_file() else list(iter_files(root_path, exts))
    if not files:
        print("No matching files found — exiting."); return

    # connect Pinecone
    pc = Pinecone(api_key=args.api_key)
    if args.index not in pc.list_indexes().names():
        pc.create_index(
            name=args.index,
            dimension=args.dim,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=region)
        )
    index = pc.Index(args.index)

    embedder = SentenceTransformer(args.model)
    ids, texts, metas = [], [], []

    for fp in tqdm(files, desc="reading files"):
        # ---- extract text -------------------------------------------
        if fp.suffix.lower() == ".pdf":
            if PdfReader is None:
                raise RuntimeError("pypdf not installed:  pip install pypdf")
            reader = PdfReader(fp)
            content = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            content = fp.read_text(encoding="utf-8", errors="ignore")

        # ---- chunk + queue ------------------------------------------
        for i, chunk in enumerate(chunk_text(content)):
            ids.append(sha1(f"{fp}:{i}"))
            texts.append(chunk)
            metas.append({"path": str(fp), "chunk": i})
            if len(ids) >= args.batch:
                flush(embedder, index, ids, texts, metas)
                ids, texts, metas = [], [], []

    if ids:
        flush(embedder, index, ids, texts, metas)

    print(f"\n✅ Done – total vectors in '{args.index}': "
          f"{index.describe_index_stats()['total_vector_count']}")

# ───────── batch-upsert helper ────────────────────────────────────────
def flush(embedder, index, ids, texts, metas):
    vecs = embedder.encode(texts, batch_size=len(texts),
                           show_progress_bar=False).tolist()
    items = [
        {
            "id": i,
            "values": v,
            "metadata": {
                "path": m["path"],
                "chunk": m["chunk"],
                "text": t           # crucial for retrieval
            }
        }
        for i, v, m, t in zip(ids, vecs, metas, texts)
    ]
    index.upsert(items)

# ───────── entry-point ────────────────────────────────────────────────
if __name__ == "__main__":
    main()
