"use client";

import { useState, useEffect, useRef } from "react";
import { ragApi, type Document } from "@/lib/api";

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const fetchDocs = async () => {
    try {
      const resp = await ragApi.list();
      setDocs(resp.data);
    } catch {
      setError("Failed to load documents.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDocs(); }, []);

  const uploadFile = async (file: File) => {
    if (!["application/pdf", "text/plain"].includes(file.type)) {
      setError("Only PDF and TXT files are supported.");
      return;
    }
    setUploading(true);
    setError(null);
    try {
      await ragApi.upload(file);
      await fetchDocs();
    } catch {
      setError("Upload failed. Please check the file and try again.");
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
    if (fileRef.current) fileRef.current.value = "";
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) uploadFile(file);
  };

  const deleteDoc = async (id: string) => {
    setDeleting(id);
    try {
      await ragApi.delete(id);
      setDocs((prev) => prev.filter((d) => d.id !== id));
    } catch {
      setError("Failed to delete document.");
    } finally {
      setDeleting(null);
    }
  };

  return (
    <main className="ml-(--spacing-sidebar-width) min-h-screen">
      <div className="pt-24 px-6 pb-10 max-w-screen-2xl mx-auto">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-on-surface">Documents</h1>
          <p className="text-sm text-on-surface-variant mt-0.5">Upload PDFs and text files for AI-powered RAG search.</p>
        </header>

        {error && (
          <p className="text-sm text-error bg-error-container/20 border border-error/30 rounded-lg px-4 py-2 mb-4">
            {error}
          </p>
        )}

        {/* Upload Dropzone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}
          className={`dotted-border rounded-xl p-10 flex flex-col items-center gap-3 cursor-pointer transition-colors mb-8 ${
            dragOver ? "bg-primary/5 border-primary" : "hover:bg-surface-container"
          }`}
        >
          <input ref={fileRef} type="file" accept=".pdf,.txt" className="hidden" onChange={handleFileChange} />
          <div className="w-14 h-14 rounded-full bg-primary-container/20 flex items-center justify-center">
            <span className="material-symbols-outlined text-2xl text-primary">
              {uploading ? "hourglass_empty" : "upload_file"}
            </span>
          </div>
          <div className="text-center">
            <p className="font-medium text-on-surface">
              {uploading ? "Uploading and indexing…" : "Drop your file here or click to browse"}
            </p>
            <p className="text-sm text-on-surface-variant mt-1">Supports PDF and TXT files up to 20 MB</p>
          </div>
        </div>

        {/* Document List */}
        <h2 className="text-sm font-semibold text-on-surface mb-3">Uploaded Documents ({docs.length})</h2>
        {loading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-14 rounded-xl bg-surface-container animate-pulse" />
            ))}
          </div>
        ) : docs.length === 0 ? (
          <div className="bg-surface-container rounded-xl border border-outline-variant p-8 text-center">
            <span className="material-symbols-outlined text-4xl text-on-surface-variant/30 mb-2">folder_open</span>
            <p className="text-sm text-on-surface-variant">No documents uploaded yet.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {docs.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center gap-4 p-4 bg-surface-container rounded-xl border border-outline-variant hover:bg-surface-container-high transition-colors"
              >
                <div className="w-10 h-10 rounded-lg bg-primary-container/20 flex items-center justify-center shrink-0">
                  <span className="material-symbols-outlined text-lg text-primary">
                    {doc.filename.endsWith(".pdf") ? "picture_as_pdf" : "article"}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-on-surface text-sm truncate">{doc.filename}</p>
                  <p className="text-xs text-on-surface-variant mt-0.5">
                    {doc.chunk_count} chunks · Uploaded {new Date(doc.created_at).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={() => deleteDoc(doc.id)}
                  disabled={deleting === doc.id}
                  className="text-on-surface-variant hover:text-error transition-colors p-1.5 rounded-lg hover:bg-error-container/20 cursor-pointer disabled:opacity-50"
                >
                  <span className="material-symbols-outlined text-lg">
                    {deleting === doc.id ? "hourglass_empty" : "delete"}
                  </span>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
