"use client";

import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import { Message } from "@/types/chat";

export default function ChatBox() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasUpload, setHasUpload] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const socket = useRef<WebSocket | null>(null);
  const isConnected = useRef(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // ── Auto scroll to bottom ──
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // ── Toast helper ──
  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  useEffect(() => {
    if (isConnected.current) return;
    isConnected.current = true;

    const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/ws/chat`);
    socket.current = ws;

    ws.onopen = () => console.log("WebSocket Connected");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "metrics") {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last?.role === "assistant") {
            updated[updated.length - 1] = {
              ...last,
              metrics: {
                response_time_ms: data.response_time_ms,
                chunks_retrieved: data.chunks_retrieved,
                compression_ratio: data.compression_ratio,
              }
            };
          }
          return updated;
        });
      }

      if (data.type === "token") {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last?.role === "assistant") {
            updated[updated.length - 1] = {
              ...last,
              content: last.content + data.content,
            };
          } else {
            updated.push({
              role: "assistant",
              content: data.content,
              sources: [],
            });
          }
          return updated;
        });
      }

      if (data.type === "end") setLoading(false);

      if (data.type === "error") {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "⚠️ " + data.content, sources: [] },
        ]);
        setLoading(false);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket Error:", error);
      setLoading(false);
    };

    ws.onclose = () => {
      console.log("WebSocket Closed");
      isConnected.current = false;
    };

    return () => { ws.close(); };
  }, []);

  // ── Listen for PDF upload and session reset ──
  useEffect(() => {
    const onUpload = () => {
      setHasUpload(true);
      showToast("✅ PDF uploaded successfully!");
    };
    const onReset = () => setHasUpload(false);

    window.addEventListener("pdf-uploaded", onUpload);
    window.addEventListener("session-reset", onReset);

    return () => {
      window.removeEventListener("pdf-uploaded", onUpload);
      window.removeEventListener("session-reset", onReset);
    };
  }, []);

  const askQuestion = () => {
    if (!question.trim()) return;
    if (!socket.current || socket.current.readyState !== WebSocket.OPEN) {
      console.error("WebSocket not connected");
      return;
    }

    const userMessage: Message = { role: "user", content: question };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    socket.current.send(question);
    setQuestion("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  };

  const startNewChat = async () => {
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/reset`, { method: "POST" });
    setMessages([]);
    setQuestion("");
    showToast("🔄 New chat started");
    window.dispatchEvent(new Event("session-reset"));
  };

  return (
    <div className="flex flex-col h-[calc(100vh-220px)]">

      {/* Toast notification */}
      {toast && (
        <div className="fixed top-4 right-4 z-50 bg-zinc-800 border border-zinc-600 text-white text-sm px-4 py-2 rounded-xl shadow-lg animate-fade-in">
          {toast}
        </div>
      )}

      {/* New Chat button */}
      <div className="flex justify-end mb-3">
        <button
          onClick={startNewChat}
          className="text-xs text-zinc-400 hover:text-white border border-zinc-700 px-3 py-1 rounded-lg transition"
        >
          + New Chat
        </button>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto space-y-6 pb-4 px-2">

        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <p className="text-4xl mb-4">📊</p>
            <h2 className="text-2xl font-semibold text-white mb-2">FinSight AI</h2>
            <p className="text-zinc-400 text-sm max-w-sm">
              {hasUpload
                ? "PDF loaded. Ask questions about revenue, risks, margins, and more."
                : "Upload a financial PDF above to start asking questions."}
            </p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-zinc-400 text-sm">
            <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" />
            <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce delay-100" />
            <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce delay-200" />
          </div>
        )}

        {/* Auto scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="mt-4">
        <div className={`flex items-end gap-3 bg-[#2f2f2f] border rounded-2xl px-4 py-3 transition ${
          hasUpload ? "border-zinc-700" : "border-zinc-800 opacity-60"
        }`}>
          <textarea
            className="flex-1 bg-transparent text-white placeholder-zinc-500 resize-none focus:outline-none text-sm leading-relaxed max-h-40 disabled:cursor-not-allowed"
            rows={1}
            value={question}
            disabled={!hasUpload || loading}
            onChange={(e) => {
              setQuestion(e.target.value);
              e.target.style.height = "auto";
              e.target.style.height = e.target.scrollHeight + "px";
            }}
            onKeyDown={handleKeyDown}
            placeholder={
              hasUpload
                ? "Ask about risks, revenue, growth..."
                : "Upload a PDF first to start chatting..."
            }
          />
          <button
            onClick={askQuestion}
            disabled={loading || !question.trim() || !hasUpload}
            className="bg-white text-black p-2 rounded-xl disabled:opacity-30 disabled:cursor-not-allowed hover:bg-zinc-200 transition shrink-0"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
              <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
            </svg>
          </button>
        </div>
        <p className="text-center text-zinc-600 text-xs mt-2">
          FinSight AI · Answers based on uploaded documents only
        </p>
      </div>

    </div>
  );
}