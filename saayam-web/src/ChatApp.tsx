import { useState, useRef, useEffect, FormEvent } from "react";
import { motion } from "framer-motion";
import { MessageSquare } from "lucide-react";

import { Card, CardContent } from "./components/ui/card";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";

interface Msg {
  role: "user" | "bot" | "src";
  text: string;
}

const API =
  (import.meta.env.VITE_API as string | undefined) ??
  "http://127.0.0.1:8000/chat";

export default function ChatApp() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  /* auto-scroll on new message */
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(e: FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (!q || pending) return;

    setMessages((m) => [...m, { role: "user", text: q }]);
    setQuestion("");
    setPending(true);

    try {
      const res = await fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      const data = await res.json();

      setMessages((m) => [
        ...m,
        { role: "bot", text: data.answer },
        ...(data.sources?.length
          ? [
              {
                role: "src",
                text: `Sources: ${data.sources.join(", ")}`,
              } as Msg,
            ]
          : []),
      ]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setMessages((m) => [...m, { role: "bot", text: `Error: ${msg}` }]);
    } finally {
      setPending(false);
    }
  }

  return (
    <Card className="w-[32rem] h-[80vh] flex flex-col shadow-xl">
      <CardContent className="flex-1 overflow-y-auto space-y-4 py-4">
        {messages.map((m, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className={
              m.role === "user"
                ? "text-right"
                : m.role === "src"
                ? "text-xs text-gray-500"
                : ""
            }
          >
            {m.text}
          </motion.div>
        ))}
        <div ref={bottomRef} />
      </CardContent>

      <form onSubmit={send} className="p-4 flex gap-2 border-t bg-white/60">
        <Input
          placeholder="Ask Saayam-for-All…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={pending}
        />
        <Button type="submit" disabled={pending}>
          <MessageSquare className="w-4 h-4 mr-1" />
          Send
        </Button>
      </form>
    </Card>
  );
}
