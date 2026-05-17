"use client";

import { useState, useEffect, useRef } from "react";
import ChatBubble from "@/components/ChatBubble";
import { chatApi, ragApi, type Document, type ChatResponse } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  hallucination_flagged?: boolean;
  timestamp: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [sessionId] = useState(() => crypto.randomUUID());
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Load documents
  useEffect(() => {
    ragApi.list().then((r) => setDocuments(r.data)).catch(() => {});
  }, []);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const resp = await chatApi.send(text, conversationId, sessionId);
      const data: ChatResponse = resp.data;
      setConversationId(data.conversation_id);
      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.answer,
        sources: data.sources,
        hallucination_flagged: data.hallucination_flagged,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "I'm having trouble right now. Please try again.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      await ragApi.upload(file);
      const r = await ragApi.list();
      setDocuments(r.data);
    } catch (err: unknown) {
      setUploadError("Upload failed. Please try again.");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  return (
    <main className="flex-1 flex flex-col ml-(--spacing-sidebar-width) h-screen relative overflow-hidden pt-16">
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel: Documents */}
        <aside className="w-64 border-r border-outline-variant bg-surface-container-low flex flex-col">
          <div className="p-4 border-b border-outline-variant">
            <h2 className="text-sm font-semibold text-on-surface">Documents</h2>
            <p className="text-xs text-on-surface-variant mt-0.5">Used for RAG answers</p>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-1">
            {documents.length === 0 && (
              <p className="text-xs text-on-surface-variant text-center py-4">No documents uploaded</p>
            )}
            {documents.map((doc) => (
              <div key={doc.id} className="flex items-center gap-2 p-2 rounded-lg hover:bg-surface-container-high text-xs text-on-surface-variant">
                <span className="material-symbols-outlined text-sm text-primary">description</span>
                <span className="truncate flex-1">{doc.filename}</span>
                <span className="shrink-0 text-on-surface-variant/50">{doc.chunk_count}c</span>
              </div>
            ))}
          </div>
          <div className="p-3 border-t border-outline-variant">
            <input ref={fileRef} type="file" accept=".pdf,.txt" className="hidden" onChange={handleUpload} />
            <button
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
              className="w-full flex items-center justify-center gap-2 py-2 rounded-lg border border-dashed border-outline-variant text-xs text-on-surface-variant hover:border-primary hover:text-primary transition-colors cursor-pointer disabled:opacity-50"
            >
              <span className="material-symbols-outlined text-sm">{uploading ? "hourglass_empty" : "upload_file"}</span>
              {uploading ? "Uploading…" : "Upload PDF / TXT"}
            </button>
            {uploadError && <p className="text-xs text-error mt-1">{uploadError}</p>}
          </div>
        </aside>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-2">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center gap-3">
                <div className="w-12 h-12 rounded-full bg-primary-container/20 flex items-center justify-center">
                  <span className="material-symbols-outlined text-2xl text-primary">smart_toy</span>
                </div>
                <div>
                  <p className="text-on-surface font-medium">BizMind AI is ready</p>
                  <p className="text-sm text-on-surface-variant mt-1">Ask anything — I can search your documents, capture leads, or answer business questions.</p>
                </div>
                <div className="flex gap-2 flex-wrap justify-center mt-2">
                  {["Summarize my latest report", "I need pricing info", "What's our return policy?"].map((s) => (
                    <button
                      key={s}
                      onClick={() => setInput(s)}
                      className="text-xs px-3 py-1.5 rounded-full border border-outline-variant text-on-surface-variant hover:border-primary hover:text-primary transition-colors cursor-pointer"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((msg) => (
              <ChatBubble
                key={msg.id}
                role={msg.role}
                content={msg.content}
                sources={msg.sources}
                hallucination_flagged={msg.hallucination_flagged}
                timestamp={msg.timestamp}
              />
            ))}
            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-surface-container-high flex items-center justify-center shrink-0">
                  <span className="material-symbols-outlined text-base text-secondary">smart_toy</span>
                </div>
                <div className="bg-surface-container border border-outline-variant rounded-2xl rounded-tl-sm px-4 py-3">
                  <div className="flex gap-1 items-center h-4">
                    {[0, 1, 2].map((i) => (
                      <div
                        key={i}
                        className="w-2 h-2 rounded-full bg-on-surface-variant animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-outline-variant">
            <div className="flex gap-2 items-end">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                placeholder="Ask BizMind AI… (Shift+Enter for new line)"
                rows={1}
                className="flex-1 resize-none px-4 py-3 rounded-xl bg-surface-container border border-outline-variant text-on-surface text-sm placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary transition-colors"
                style={{ maxHeight: "120px" }}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || loading}
                className="p-3 rounded-xl bg-primary text-on-primary hover:opacity-90 active:scale-95 transition-all disabled:opacity-40 cursor-pointer"
              >
                <span className="material-symbols-outlined">send</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
