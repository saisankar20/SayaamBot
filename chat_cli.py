#!/usr/bin/env python
# chat_cli.py – simple REPL client for the FastAPI chatbot

import requests, json, sys

API_URL = "http://127.0.0.1:8000/chat"

print("Saayam Chat – type 'exit' to quit\n")

while True:
    q = input("You: ").strip()
    if q.lower() in {"exit", "quit"}:
        sys.exit(0)

    try:
        resp = requests.post(API_URL, json={"question": q}, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        print("\nBot:", data["answer"])
        if data.get("sources"):
            print("Sources:", ", ".join(data["sources"]))
    except Exception as e:
        print("⚠️  error:", e)
    print()
