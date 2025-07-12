#!/usr/bin/env python
import requests, sys, json
API="http://127.0.0.1:8000/chat"
print("Saayam Chat — type 'exit' to quit")

while True:
    q=input("You: ").strip()
    if q.lower() in {"exit","quit"}: sys.exit(0)
    r=requests.post(API,json={"question":q},timeout=60)
    try:
        r.raise_for_status()
        data=r.json()
        print("\nBot:",data['answer'])
        if data.get("sources"): print("Sources:",", ".join(data["sources"]))
    except Exception as e:
        print("⚠️ error",e)
    print()
