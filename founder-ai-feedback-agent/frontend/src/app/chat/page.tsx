"use client";
import { useState, useRef, useEffect } from "react";
import { chatAPI } from "@/lib/api";
import { Send, Bot, User, Loader } from "lucide-react";
import { cn } from "@/lib/utils";

interface Message { role: "user" | "assistant"; content: string; model?: string; }

const SUGGESTED = [
  "What are customers complaining about most?",
  "What features are users requesting?",
  "Why is sentiment dropping?",
  "What is our most critical issue right now?",
  "Give me an executive summary of recent feedback.",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([{
    role: "assistant",
    content: "Hi! I'm your Feedback Intelligence AI. I can analyze your customer feedback and answer questions about sentiment, complaints, feature requests, and business trends. What would you like to know?",
  }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput("");
    setMessages(m => [...m, { role: "user", content: msg }]);
    setLoading(true);
    try {
      const res = await chatAPI.send(msg);
      setMessages(m => [...m, { role: "assistant", content: res.data.answer, model: res.data.model }]);
    } catch (e: any) {
      setMessages(m => [...m, { role: "assistant", content: "Sorry, I encountered an error. Please check your LLM configuration and try again." }]);
    } finally { setLoading(false); }
  };

  return (
    <div className="flex flex-col h-screen">
      <div className="p-6 border-b border-slate-100 bg-white">
        <h1 className="text-xl font-bold text-slate-900">AI Feedback Chat</h1>
        <p className="text-slate-500 text-sm">Ask anything about your customer feedback data</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={cn("flex gap-3", m.role === "user" ? "justify-end" : "justify-start")}>
            {m.role === "assistant" && (
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <Bot className="w-4 h-4 text-white" />
              </div>
            )}
            <div className={cn("max-w-xl rounded-2xl px-4 py-3 text-sm leading-relaxed",
              m.role === "user" ? "bg-blue-600 text-white rounded-br-sm" : "bg-white border border-slate-100 text-slate-800 rounded-bl-sm shadow-sm")}>
              <p className="whitespace-pre-wrap">{m.content}</p>
              {m.model && <p className="text-xs opacity-50 mt-2">via {m.model}</p>}
            </div>
            {m.role === "user" && (
              <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <User className="w-4 h-4 text-white" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="bg-white border border-slate-100 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
              <Loader className="w-4 h-4 text-blue-500 animate-spin" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {messages.length === 1 && (
        <div className="px-6 pb-4">
          <p className="text-xs text-slate-400 mb-2 font-medium">Suggested questions</p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED.map((q, i) => (
              <button key={i} onClick={() => send(q)}
                className="text-xs bg-white border border-slate-200 rounded-full px-3 py-1.5 text-slate-600 hover:border-blue-400 hover:text-blue-600 transition-colors">
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="p-4 border-t border-slate-100 bg-white">
        <div className="flex gap-3 max-w-3xl mx-auto">
          <input className="input flex-1" value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && !e.shiftKey && send()}
            placeholder="Ask about your customer feedback..." disabled={loading} />
          <button onClick={() => send()} disabled={loading || !input.trim()}
            className="btn-primary flex items-center gap-2">
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
