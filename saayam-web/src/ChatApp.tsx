import { useState, useRef, useEffect } from "react";
import { Card, CardContent } from "./components/ui/card";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { MessageSquare } from "lucide-react";
import { motion } from "framer-motion";

interface Msg { role: "user" | "bot" | "src"; text: string; }
const API = import.meta.env.VITE_API ?? "http://127.0.0.1:8000/chat";

export default function ChatApp() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [pending, setPending] = useState(false);
  const [question, setQuestion] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(e?: React.FormEvent) {
    e?.preventDefault();
    if (!question.trim() || pending) return;
    const q = question.trim();
    setQuestion("");
    setMessages(m => [...m, { role: "user", text: q }]);
    setPending(true);
    try {
      const r = await fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      const data = await r.json();
      setMessages(m => [
        ...m,
        { role: "bot", text: data.answer },
        ...(data.sources?.length
          ? [{ role: "src", text: `Sources: ${data.sources.join(", ")}` }]
          : []),
      ]);
    } catch (err: any) {
      setMessages(m => [...m, { role: "bot", text: `Error: ${err.message}` }]);
    } finally {
      setPending(false);
    }
  }

  return (
    <Card className="w-full max-w-lg h-[80vh] flex flex-col shadow-xl bg-white mx-auto">
      <CardContent className="flex-1 overflow-y-auto space-y-4 py-4">
        {messages.map((m, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={
              m.role === "user"
                ? "text-right text-gray-800"
                : m.role === "src"
                ? "text-xs text-gray-500"
                : "text-gray-900"
            }
          >
            {m.text}
          </motion.div>
        ))}
        <div ref={bottomRef} />
      </CardContent>
      <form onSubmit={send} className="p-4 flex gap-2 border-t bg-gray-100">
        <Input
          className="flex-1 text-black bg-white placeholder-gray-500
                     border border-gray-300 focus:ring focus:ring-indigo-200"
          value={question}
          onChange={e => setQuestion(e.target.value)}
          placeholder="Ask Saayam-for-All…"
          disabled={pending}
        />
        <Button disabled={pending} type="submit">
          <MessageSquare className="w-4 h-4 mr-1" /> Send
        </Button>
      </form>
    </Card>
  );
}
