"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import MessageBubble from "./MessageBubble";
import { Message } from "@/types/chat";

const WS_URL = `${process.env.NEXT_PUBLIC_WS_URL}/ws/chat`;
const RECONNECT_MAX_DELAY_MS = 16000;

export default function ChatBox() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasUpload, setHasUpload] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState<"connecting" | "open" | "closed">("connecting");

  const socket = useRef<WebSocket | null>(null);
  const reconnectDelay = useRef(1000);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const unmounted = useRef(false);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  const connect = useCallback(() => {
    if (unmounted.current) return;

    setWsStatus("connecting");
    const ws = new WebSocket(WS_URL);
    socket.current = ws;

    ws.onopen = () => {
      console.log("WebSocket Connected");
      setWsStatus("open");
      reconnectDelay.current = 1000;
    };

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
                faiss_chunks: data.faiss_chunks,
                bm25_chunks: data.bm25_chunks,
                total_retrieved: data.total_retrieved,
                after_filter: data.after_filter,
                after_dedup: data.after_dedup,
                after_rerank: data.after_rerank,
                context_chars_before: data.context_chars_before,
                context_chars_after: data.context_chars_after,
                compression_ratio: data.compression_ratio,
                filter_applied: data.filter_applied,
              },
            };
          }
          return updated;
        });
      }

      if (data.type === "sources") {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last?.role === "assistant") {
            updated[updated.length - 1] = { ...last, sources: data.sources };
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
      setWsStatus("closed");
      setLoading(false);
      if (!unmounted.current) {
        const delay = reconnectDelay.current;
        reconnectDelay.current = Math.min(delay * 2, RECONNECT_MAX_DELAY_MS);
        setTimeout(connect, delay);
      }
    };
  }, []);

  useEffect(() => {
    unmounted.current = false;
    connect();
    return () => {
      unmounted.current = true;
      socket.current?.close();
    };
  }, [connect]);

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
      showToast("⚠️ Not connected — reconnecting…");
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

  const isReady = wsStatus === "open" && hasUpload;

  return (
    <div className="flex flex-col h-[calc(100vh-220px)]">

      {toast && (
        <div className="fixed top-4 right-4 z-50 bg-zinc-800 border border-zinc-600 text-white text-sm px-4 py-2 rounded-xl shadow-lg animate-fade-in">
          {toast}
        </div>
      )}

      <div className="flex justify-between items-center mb-3">
        {wsStatus === "closed" && (
          <span className="text-xs text-red-400 animate-pulse">● Reconnecting…</span>
        )}
        {wsStatus === "connecting" && (
          <span className="text-xs text-yellow-400 animate-pulse">● Connecting…</span>
        )}
        {wsStatus === "open" && <span />}
        <button
          onClick={startNewChat}
          className="text-xs text-zinc-400 hover:text-white border border-zinc-700 px-3 py-1 rounded-lg transition"
        >
          + New Chat
        </button>
      </div>

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

        <div ref={messagesEndRef} />
      </div>

      <div className="mt-4">
        <div className={`flex items-end gap-3 bg-[#2f2f2f] border rounded-2xl px-4 py-3 transition ${
          isReady ? "border-zinc-700" : "border-zinc-800 opacity-60"
        }`}>
          <textarea
            className="flex-1 bg-transparent text-white placeholder-zinc-500 resize-none focus:outline-none text-sm leading-relaxed max-h-40 disabled:cursor-not-allowed"
            rows={1}
            value={question}
            disabled={!isReady || loading}
            onChange={(e) => {
              setQuestion(e.target.value);
              e.target.style.height = "auto";
              e.target.style.height = e.target.scrollHeight + "px";
            }}
            onKeyDown={handleKeyDown}
            placeholder={
              !hasUpload
                ? "Upload a PDF first to start chatting..."
                : wsStatus !== "open"
                ? "Reconnecting to server…"
                : "Ask about risks, revenue, growth..."
            }
          />
          <button
            onClick={askQuestion}
            disabled={loading || !question.trim() || !isReady}
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
