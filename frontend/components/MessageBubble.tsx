"use client";

import ReactMarkdown from "react-markdown";
import { Message } from "@/types/chat";
import CitationCard from "./CitationCard";

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 mb-4 ${isUser ? "justify-end" : "justify-start"}`}>
      {/* AI Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-white text-black flex items-center justify-center text-xs font-bold shrink-0 mt-1">
          F
        </div>
      )}

      <div
        className={`max-w-[80%] flex flex-col gap-2 ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? "bg-[#2f2f2f] text-white rounded-tr-sm"
              : "bg-transparent text-zinc-100"
          }`}
        >
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <ReactMarkdown
              components={{
                h1: ({ children }) => (
                  <h1 className="text-xl font-bold mb-2 text-white">
                    {children}
                  </h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-lg font-bold mb-2 text-white">
                    {children}
                  </h2>
                ),
                strong: ({ children }) => (
                  <strong className="font-bold text-white">
                    {children}
                  </strong>
                ),
                p: ({ children }) => (
                  <p className="mb-3 leading-relaxed">{children}</p>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc list-inside mb-3 space-y-1">
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-inside mb-3 space-y-1">
                    {children}
                  </ol>
                ),
                li: ({ children }) => (
                  <li className="text-zinc-200">{children}</li>
                ),
                hr: () => <hr className="border-zinc-600 my-3" />,
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {/* RAG Pipeline Metrics */}
        {!isUser && message.metrics && (
          <div className="mt-2 text-[11px] text-zinc-600 space-y-1 font-mono">
            {/* Pipeline flow */}
            <div className="flex flex-wrap items-center gap-1">
              <span className="text-zinc-500">FAISS</span>
              <span className="text-zinc-400 font-semibold">{message.metrics.faiss_chunks}</span>
              <span className="text-zinc-700">+</span>
              <span className="text-zinc-500">BM25</span>
              <span className="text-zinc-400 font-semibold">{message.metrics.bm25_chunks}</span>
              <span className="text-zinc-700 mx-1">→</span>
              <span className="text-zinc-500">dedup</span>
              <span className="text-zinc-400 font-semibold">{message.metrics.after_dedup}</span>
              <span className="text-zinc-700 mx-1">→</span>
              <span className="text-zinc-500">reranked</span>
              <span className="text-zinc-400 font-semibold">{message.metrics.after_rerank}</span>
            </div>
            {/* Compression + latency */}
            <div className="flex flex-wrap items-center gap-3">
              <span>
                <span className="text-zinc-500">context </span>
                <span className="text-zinc-400">{message.metrics.context_chars_before.toLocaleString()}</span>
                <span className="text-zinc-700"> → </span>
                <span className="text-zinc-400">{message.metrics.context_chars_after.toLocaleString()}</span>
                <span className="text-zinc-500"> chars</span>
                <span className="text-emerald-700 ml-1">
                  ({Math.round((1 - message.metrics.compression_ratio) * 100)}% reduction)
                </span>
              </span>
              <span className="text-zinc-700">·</span>
              <span>
                <span className="text-zinc-500">latency </span>
                <span className="text-zinc-400">{message.metrics.response_time_ms.toLocaleString()}ms</span>
              </span>
            </div>
          </div>
        )}

        {/* Citations */}
        {!isUser &&
          message.sources?.map((source, idx) => (
            <CitationCard key={idx} source={source} />
          ))}
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-zinc-600 text-white flex items-center justify-center text-xs font-bold shrink-0 mt-1">
          U
        </div>
      )}
    </div>
  );
}