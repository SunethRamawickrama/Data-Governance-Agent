"use client";
import { useState } from "react";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
    }
  };

  const handleUpload = () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    console.log("Uploading:", file);

    fetch("http://127.0.0.1:8000/api/upload", {
      method: "POST",
      body: formData,
    })
      .then((res) => res.json())
      .then((data) => alert(data.message))
      .catch((err) => console.error("Upload error:", err));
  };

  return (
    <main className="flex flex-col items-center justify-center h-screen gap-6 px-4">
      <h1 className="text-2xl font-bold">Upload a File</h1>

      <input
        type="file"
        onChange={handleFileChange}
        className="block w-full max-w-sm text-sm text-gray-500
                   file:mr-4 file:py-2 file:px-4
                   file:rounded-md file:border-0
                   file:text-sm file:font-semibold
                   file:bg-blue-50 file:text-blue-700
                   hover:file:bg-blue-100"
      />

      {file && <p className="text-gray-600">Selected: {file.name}</p>}

      <button
        onClick={handleUpload}
        className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Upload
      </button>
    </main>
  );
}
