"use client";

import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import { Message } from "@/types/chat";

export default function ChatBox() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const socket = useRef<WebSocket | null>(null);
  const isConnected = useRef(false);

  useEffect(() => {
    if (isConnected.current) return;
    isConnected.current = true;

    const ws = new WebSocket("ws://localhost:8000/ws/chat");
    socket.current = ws;

    ws.onopen = () => {
      console.log("WebSocket Connected");
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

      if (data.type === "end") {
        setLoading(false);
      }

      if (data.type === "error") {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "⚠️ " + data.content,
            sources: [],
          },
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

    return () => {
      ws.close();
    };
  }, []);

  const askQuestion = () => {
    if (!question.trim()) return;

    if (!socket.current || socket.current.readyState !== WebSocket.OPEN) {
      console.error("WebSocket not connected");
      return;
    }

    const userMessage: Message = {
      role: "user",
      content: question,
    };

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
    await fetch("http://localhost:8000/reset", { method: "POST" });
    setMessages([]);
    setQuestion("");
    window.dispatchEvent(new Event("session-reset"));
  };

  return (
    <div className="flex flex-col h-[calc(100vh-220px)]">
      
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
            <h2 className="text-2xl font-semibold text-white mb-2">
              FinSight AI
            </h2>
            <p className="text-zinc-400 text-sm max-w-sm">
              Upload a financial PDF and ask questions about revenue, risks, margins, and more.
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

      </div>

      {/* Input area — fixed at bottom like GPT */}
      <div className="mt-4">
        <div className="flex items-end gap-3 bg-[#2f2f2f] border border-zinc-700 rounded-2xl px-4 py-3">
          <textarea
            className="flex-1 bg-transparent text-white placeholder-zinc-500 resize-none focus:outline-none text-sm leading-relaxed max-h-40"
            rows={1}
            value={question}
            onChange={(e) => {
              setQuestion(e.target.value);
              e.target.style.height = "auto";
              e.target.style.height = e.target.scrollHeight + "px";
            }}
            onKeyDown={handleKeyDown}
            placeholder="Ask about risks, revenue, growth..."
          />
          <button
            onClick={askQuestion}
            disabled={loading || !question.trim()}
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