"use client";

import { useRef, useState } from "react";

interface CVUploadProps {
  currentFilename: string | null;
  onUpload: (file: File) => Promise<void>;
  loading: boolean;
}

const ACCEPTED_TYPES = ".pdf,.docx,.md";
const MAX_SIZE_MB = 10;

export default function CVUpload({ currentFilename, onUpload, loading }: CVUploadProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    setError("");
    const file = e.target.files?.[0];
    if (!file) return;

    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!ext || !["pdf", "docx", "md"].includes(ext)) {
      setError("Only PDF, DOCX, and Markdown files are allowed.");
      return;
    }

    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File too large. Maximum size is ${MAX_SIZE_MB}MB.`);
      return;
    }

    setSelectedFile(file);
  }

  async function handleUpload() {
    if (!selectedFile) return;
    setError("");
    try {
      await onUpload(selectedFile);
      setSelectedFile(null);
      if (fileRef.current) fileRef.current.value = "";
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Upload failed.");
      }
    }
  }

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-gray-700">CV Upload</label>

      {currentFilename && (
        <p className="text-sm text-gray-600">
          Current file: <span className="font-medium text-gray-900">{currentFilename}</span>
        </p>
      )}

      <div className="flex items-center gap-3">
        <input
          ref={fileRef}
          type="file"
          accept={ACCEPTED_TYPES}
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-900 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
        <button
          type="button"
          onClick={handleUpload}
          disabled={!selectedFile || loading}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
        >
          {loading ? "Uploading..." : "Upload"}
        </button>
      </div>

      <p className="text-xs text-gray-400">Accepted: PDF, DOCX, Markdown. Max 10MB.</p>

      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
