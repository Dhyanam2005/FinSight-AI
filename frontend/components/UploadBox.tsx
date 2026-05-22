"use client";

import { useState } from "react";
import API from "@/lib/api";

export default function UploadBox() {
  const [loading, setLoading] = useState(false);

  const handleUpload = async (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);

      await API.post("/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      alert("Upload successful!");
    } catch (err) {
      console.error(err);
      alert("Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border rounded-2xl p-6 shadow-sm bg-white">
      <h2 className="text-xl font-semibold mb-4">
        Upload Financial Document
      </h2>

      <input
        type="file"
        accept=".pdf"
        onChange={handleUpload}
      />

      {loading && (
        <p className="mt-2 text-sm text-gray-500">
          Processing PDF...
        </p>
      )}
    </div>
  );
}