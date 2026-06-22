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

        {/* RAG Metrics */}
        {!isUser && message.metrics && (
          <div className="flex flex-wrap gap-4 mt-1 text-xs text-zinc-500">
            <span>
              ⚡ {message.metrics.response_time_ms}ms
            </span>

            <span>
              📄 {message.metrics.chunks_retrieved} chunks
            </span>

            {message.metrics.compression_ratio !== undefined && (
              <span>
                🗜️ {message.metrics.compression_ratio}x compressed
              </span>
            )}
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