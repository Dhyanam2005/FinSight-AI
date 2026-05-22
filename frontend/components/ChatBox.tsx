"use client";

import { useState } from "react";
import API from "@/lib/api";
import MessageBubble from "./MessageBubble";
import { Message } from "@/types/chat";

export default function ChatBox() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const askQuestion = async () => {
    if (!question.trim()) return;

    const userMessage: Message = {
      role: "user",
      content: question,
    };

    setMessages((prev) => [...prev, userMessage]);

    const currentQuestion = question;
    setQuestion("");

    try {
      setLoading(true);

      const res = await API.post("/ask", {
        question: currentQuestion,
      });

      const aiMessage: Message = {
        role: "assistant",
        content: res.data.answer,
        sources: res.data.sources,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
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