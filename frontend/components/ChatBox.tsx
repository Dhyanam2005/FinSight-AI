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
  };

  return (
    <div className="border rounded-2xl p-6 bg-white shadow-sm">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">
          Financial Research Chat
        </h2>

        <button
          onClick={startNewChat}
          className="text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-lg"
        >
          + New Chat
        </button>
      </div>

      <div className="h-[500px] overflow-y-auto border rounded-xl p-4 mb-4 bg-gray-50">
        {messages.length === 0 && (
          <p className="text-gray-500 text-sm">
            Ask questions about uploaded financial documents...
          </p>
        )}

        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}

        {loading && (
          <p className="text-sm text-gray-500 animate-pulse">
            Thinking...
          </p>
        )}
      </div>

      <textarea
        className="w-full border rounded-lg p-3"
        rows={3}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about risks, revenue, growth..."
      />

      <button
        onClick={askQuestion}
        disabled={loading || !question.trim()}
        className="mt-4 bg-black text-white px-4 py-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? "Thinking..." : "Ask"}
      </button>
    </div>
  );
}