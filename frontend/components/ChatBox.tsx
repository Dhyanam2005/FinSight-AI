"use client";

import { useEffect, useRef, useState } from "react";

import MessageBubble from "./MessageBubble";
import { Message } from "@/types/chat";

export default function ChatBox() {

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const socket = useRef<WebSocket | null>(null);

  useEffect(() => {

    socket.current = new WebSocket(
      "ws://localhost:8000/ws/chat"
    );

    socket.current.onopen = () => {
      console.log("WebSocket Connected");
    };

    socket.current.onmessage = (event) => {

      const data = JSON.parse(event.data);

      // Stream tokens
      if (data.type === "token") {

        setMessages((prev) => {

          const updated = [...prev];

          const lastMessage = updated[updated.length - 1];

          // Continue existing assistant message
          if (lastMessage?.role === "assistant") {

            lastMessage.content += data.content;
          }

          // First streamed token
          else {

            updated.push({
              role: "assistant",
              content: data.content,
              sources: [],
            });
          }

          return [...updated];
        });
      }

      // Streaming finished
      if (data.type === "end") {

        setLoading(false);
      }
    };

    socket.current.onerror = (error) => {
      console.error("WebSocket Error:", error);
      setLoading(false);
    };

    socket.current.onclose = () => {
      console.log("WebSocket Closed");
    };

    return () => {
      socket.current?.close();
    };

  }, []);

  const askQuestion = async () => {

    if (!question.trim()) return;

    // Add user message
    const userMessage: Message = {
      role: "user",
      content: question,
    };

    setMessages((prev) => [...prev, userMessage]);

    setLoading(true);

    // Send question through websocket
    socket.current?.send(question);

    setQuestion("");
  };

  return (

    <div className="border rounded-2xl p-6 bg-white shadow-sm">

      <h2 className="text-xl font-semibold mb-4">
        Financial Research Chat
      </h2>

      <div className="h-[500px] overflow-y-auto border rounded-xl p-4 mb-4 bg-gray-50">

        {messages.length === 0 && (
          <p className="text-gray-500 text-sm">
            Ask questions about uploaded financial documents...
          </p>
        )}

        {messages.map((msg, idx) => (
          <MessageBubble
            key={idx}
            message={msg}
          />
        ))}

        {loading && (
          <p className="text-sm text-gray-500">
            Thinking...
          </p>
        )}

      </div>

      <textarea
        className="w-full border rounded-lg p-3"
        rows={3}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask about risks, revenue, growth..."
      />

      <button
        onClick={askQuestion}
        className="mt-4 bg-black text-white px-4 py-2 rounded-lg"
      >
        Ask
      </button>

    </div>
  );
}