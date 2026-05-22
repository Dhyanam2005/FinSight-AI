"use client";

import { useState } from "react";
import API from "@/lib/api";

export default function UploadBox() {

  const [loading, setLoading] = useState(false);

  const handleUpload = async (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {

    const files = e.target.files;

    if (!files || files.length === 0) return;

    try {

      setLoading(true);

      // Upload all selected PDFs
      for (let i = 0; i < files.length; i++) {

        const formData = new FormData();

        formData.append("file", files[i]);

        await API.post("/upload", formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });
      }

      alert("All PDFs uploaded successfully!");

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
        Upload Financial Documents
      </h2>

      <input
        type="file"
        accept=".pdf"
        multiple
        onChange={handleUpload}
      />

      {loading && (
        <p className="mt-2 text-sm text-gray-500">
          Processing PDFs...
        </p>
      )}

    </div>
  );
}