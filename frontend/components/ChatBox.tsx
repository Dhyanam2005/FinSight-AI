"use client";

import { useState } from "react";
import API from "@/lib/api";

export default function ChatBox() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  const askQuestion = async () => {
    try {
      const res = await API.post("/ask", {
        question,
      });

      setAnswer(res.data.answer);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="border rounded-2xl p-6 bg-white shadow-sm">
      <h2 className="text-xl font-semibold mb-4">
        Ask Questions
      </h2>

      <textarea
        className="w-full border rounded-lg p-3"
        rows={4}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask about revenue, risks, guidance..."
      />

      <button
        onClick={askQuestion}
        className="mt-4 bg-black text-white px-4 py-2 rounded-lg"
      >
        Ask
      </button>

      {answer && (
        <div className="mt-6 p-4 border rounded-lg bg-gray-50">
          {answer}
        </div>
      )}
    </div>
  );
}