"use client";

import { useState, useRef } from "react";
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

  // ✅ Cycles through steps for a given file index
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

  const handleUpload = async (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);

    // ✅ Add new files to existing list (don't replace)
    const newFiles: UploadedFile[] = Array.from(files).map((f) => ({
      name: f.name,
      status: "pending",
      step: "Waiting...",
    }));

    setUploadedFiles((prev) => [...prev, ...newFiles]);

    const startIndex = uploadedFiles.length;

    for (let i = 0; i < files.length; i++) {
      const fileIndex = startIndex + i;

      // Mark as processing
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

        // Mark as done
        setUploadedFiles((prev) => {
          const updated = [...prev];
          updated[fileIndex] = {
            ...updated[fileIndex],
            status: "done",
            step: "Ready!",
          };
          return updated;
        });

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

    // ✅ Reset input so same file can be re-uploaded
    if (inputRef.current) inputRef.current.value = "";
    setIsUploading(false);
  };

  const removeFile = (index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const statusColor = (status: UploadedFile["status"]) => {
    if (status === "done") return "text-green-600";
    if (status === "error") return "text-red-500";
    if (status === "processing") return "text-blue-500";
    return "text-gray-400";
  };

  const statusIcon = (status: UploadedFile["status"]) => {
    if (status === "done") return "✅";
    if (status === "error") return "❌";
    if (status === "processing") return "⏳";
    return "📄";
  };

  return (
    <div className="border rounded-2xl p-6 shadow-sm bg-white">

      <h2 className="text-xl font-semibold mb-4">
        Upload Financial Documents
      </h2>

      {/* Drop zone */}
      <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-xl cursor-pointer hover:border-black hover:bg-gray-50 transition-all">
        <span className="text-3xl mb-1">📂</span>
        <span className="text-sm text-gray-500">
          {isUploading ? "Uploading..." : "Click to upload PDFs"}
        </span>
        <span className="text-xs text-gray-400 mt-1">
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

      {/* File list */}
      {uploadedFiles.length > 0 && (
        <div className="mt-4 space-y-2">
          {uploadedFiles.map((file, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between border rounded-lg px-4 py-2 bg-gray-50"
            >
              <div className="flex items-center gap-3 min-w-0">
                <span>{statusIcon(file.status)}</span>
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate max-w-[200px]">
                    {file.name}
                  </p>
                  <p className={`text-xs ${statusColor(file.status)}`}>
                    {file.status === "processing" && (
                      <span className="animate-pulse">{file.step}</span>
                    )}
                    {file.status !== "processing" && file.step}
                  </p>
                </div>
              </div>

              {/* Progress bar for processing */}
              {file.status === "processing" && (
                <div className="w-24 h-1.5 bg-gray-200 rounded-full overflow-hidden mx-3">
                  <div className="h-full bg-black rounded-full animate-[progress_10s_linear_forwards]" />
                </div>
              )}

              {/* Remove button for done/error */}
              {(file.status === "done" || file.status === "error") && (
                <button
                  onClick={() => removeFile(idx)}
                  className="text-gray-400 hover:text-red-500 text-xs ml-3 shrink-0"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Add progress animation to tailwind */}
      <style>{`
        @keyframes progress {
          from { width: 0% }
          to { width: 100% }
        }
      `}</style>

    </div>
  );
}