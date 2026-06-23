"use client";

import { useState, useRef, useEffect } from "react";
import API from "@/lib/api";

interface UploadedFile {
  name: string;
  status: "pending" | "processing" | "done" | "error";
  step: string;
}

const STEPS = [
  "Parsing PDF...",
  "Chunking text...",
  "Analyzing sentiment...",
  "Building embeddings...",
  "Indexing...",
];

export default function UploadBox() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // ── Clear files on session reset ──
  useEffect(() => {
    const onReset = () => setUploadedFiles([]);
    window.addEventListener("session-reset", onReset);
    return () => window.removeEventListener("session-reset", onReset);
  }, []);

  const cycleSteps = (fileIndex: number): NodeJS.Timeout => {
    let stepIndex = 0;

    const interval = setInterval(() => {
      stepIndex++;
      if (stepIndex >= STEPS.length) {
        clearInterval(interval);
        return;
      }

      setUploadedFiles((prev) => {
        const updated = [...prev];
        if (updated[fileIndex]) {
          updated[fileIndex] = {
            ...updated[fileIndex],
            step: STEPS[stepIndex],
          };
        }
        return updated;
      });
    }, 2500);

    return interval;
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);

    const newFiles: UploadedFile[] = Array.from(files).map((f) => ({
      name: f.name,
      status: "pending",
      step: "Waiting...",
    }));

    const startIndex = uploadedFiles.length;
    setUploadedFiles((prev) => [...prev, ...newFiles]);

    for (let i = 0; i < files.length; i++) {
      const fileIndex = startIndex + i;

      setUploadedFiles((prev) => {
        const updated = [...prev];
        updated[fileIndex] = {
          ...updated[fileIndex],
          status: "processing",
          step: STEPS[0],
        };
        return updated;
      });

      const interval = cycleSteps(fileIndex);

      try {
        const formData = new FormData();
        formData.append("file", files[i]);

        await API.post("/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });

        clearInterval(interval);

        setUploadedFiles((prev) => {
          const updated = [...prev];
          updated[fileIndex] = {
            ...updated[fileIndex],
            status: "done",
            step: "Ready!",
          };
          return updated;
        });

        window.dispatchEvent(new Event("pdf-uploaded"));

      } catch (err) {
        clearInterval(interval);
        console.error(err);

        setUploadedFiles((prev) => {
          const updated = [...prev];
          updated[fileIndex] = {
            ...updated[fileIndex],
            status: "error",
            step: "Upload failed",
          };
          return updated;
        });
      }
    }

    if (inputRef.current) inputRef.current.value = "";
    setIsUploading(false);
  };

  const removeFile = (index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const statusColor = (status: UploadedFile["status"]) => {
    if (status === "done") return "text-green-500";
    if (status === "error") return "text-red-500";
    if (status === "processing") return "text-blue-400";
    return "text-zinc-400";
  };

  const statusIcon = (status: UploadedFile["status"]) => {
    if (status === "done") return "✅";
    if (status === "error") return "❌";
    if (status === "processing") return "⏳";
    return "📄";
  };

  return (
    <div className="border border-zinc-700 rounded-2xl p-5 bg-[#2f2f2f]">
      <h2 className="text-base font-semibold mb-3 text-white">
        Upload Financial Documents
      </h2>

      <label className="flex flex-col items-center justify-center w-full h-24 border-2 border-dashed border-zinc-600 rounded-xl cursor-pointer hover:border-zinc-400 hover:bg-zinc-700/30 transition-all">
        <span className="text-3xl mb-1">📂</span>
        <span className="text-sm text-zinc-300">
          {isUploading ? "Uploading..." : "Click to upload PDFs"}
        </span>
        <span className="text-xs text-zinc-500 mt-1">
          You can keep adding more PDFs anytime
        </span>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          multiple
          className="hidden"
          onChange={handleUpload}
          disabled={isUploading}
        />
      </label>

      {uploadedFiles.length > 0 && (
        <div className="mt-4 space-y-2">
          {uploadedFiles.map((file, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between border border-zinc-700 rounded-lg px-4 py-2 bg-[#212121]"
            >
              <div className="flex items-center gap-3 min-w-0">
                <span>{statusIcon(file.status)}</span>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-white truncate max-w-[220px]">
                    {file.name}
                  </p>
                  <p className={`text-xs ${statusColor(file.status)}`}>
                    {file.status === "processing" ? (
                      <span className="animate-pulse">{file.step}</span>
                    ) : (
                      file.step
                    )}
                  </p>
                </div>
              </div>

              {file.status === "processing" && (
                <div className="w-24 h-1.5 bg-zinc-700 rounded-full overflow-hidden mx-3">
                  <div className="h-full bg-white rounded-full animate-[progress_10s_linear_forwards]" />
                </div>
              )}

              {(file.status === "done" || file.status === "error") && (
                <button
                  onClick={() => removeFile(idx)}
                  className="text-zinc-500 hover:text-red-500 text-xs ml-3 shrink-0"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      <style>{`
        @keyframes progress {
          from { width: 0% }
          to { width: 100% }
        }
      `}</style>
    </div>
  );
}