"use client";

import { useState, useEffect, useRef } from "react";
import ChatBubble from "@/components/ChatBubble";
import { chatApi, ragApi, type Document, type ChatResponse } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  images?: string[];
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
  const [attachedImage, setAttachedImage] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const imageRef = useRef<HTMLInputElement>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Load documents and history
  useEffect(() => {
    ragApi.list().then((r) => setDocuments(r.data)).catch(() => {});
    
    chatApi.history().then((r) => {
      if (r.data.conversation_id) {
        setConversationId(r.data.conversation_id);
      }
      if (r.data.messages && r.data.messages.length > 0) {
        const formattedHistory = r.data.messages.map((m: any) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          timestamp: m.created_at,
          // Extract sources if they exist (requires parsing content or assuming they don't have sources array in DB)
        }));
        setMessages(formattedHistory);
      }
    }).catch(() => {});
  }, []);

  const sendMessage = async () => {
    const text = input.trim();
    if ((!text && !attachedImage) || loading) return;
    setInput("");
    const imgToSend = attachedImage ? [attachedImage] : [];
    setAttachedImage(null);

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      images: imgToSend,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    const assistantId = crypto.randomUUID();
    const assistantMsg: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      const resp = await chatApi.sendStream(text, imgToSend, conversationId, sessionId);
      if (!resp.body) throw new Error("No response body");
      
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      setLoading(false); // Hide standard loading indicator since we stream
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const parsed = JSON.parse(line);
            if (parsed.type === "chunk") {
              setMessages((prev) => 
                prev.map(m => m.id === assistantId ? { ...m, content: m.content + parsed.content } : m)
              );
            } else if (parsed.type === "done") {
              setConversationId(parsed.conversation_id);
              setMessages((prev) => 
                prev.map(m => m.id === assistantId ? {
                  ...m,
                  content: parsed.answer,
                  sources: parsed.sources,
                  hallucination_flagged: parsed.hallucination_flagged
                } : m)
              );
            }
          } catch (e) {
            console.error("Failed to parse chunk", line);
          }
        }
      }
    } catch {
      setMessages((prev) => prev.map(m => m.id === assistantId ? { ...m, content: m.content || "I'm having trouble right now. Please try again." } : m));
    } finally {
      setLoading(false);
    }
  };

  const handleImageAttach = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      if (ev.target?.result) {
        setAttachedImage(ev.target.result as string);
      }
    };
    reader.readAsDataURL(file);
    if (imageRef.current) imageRef.current.value = "";
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

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunks.current = [];
      
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.current.push(e.data);
      };
      
      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks.current, { type: "audio/webm" });
        const file = new File([audioBlob], "recording.webm", { type: "audio/webm" });
        
        // Ensure UI doesn't hang
        const prevInput = input;
        setInput((prev) => prev + (prev ? " " : "") + "[Transcribing...]");
        
        try {
          const resp = await chatApi.transcribe(file);
          setInput(prevInput + (prevInput ? " " : "") + resp.data.text);
        } catch (e) {
          console.error("Transcription failed", e);
          setInput(prevInput);
          alert("Transcription failed. Is GROQ_API_KEY configured?");
        }
        
        stream.getTracks().forEach((t) => t.stop());
      };
      
      recorder.start();
      mediaRecorder.current = recorder;
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access denied", err);
      alert("Microphone access denied.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      setIsRecording(false);
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
                images={msg.images}
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
            {attachedImage && (
              <div className="mb-3 relative inline-block">
                <img src={attachedImage} alt="Attached" className="h-16 w-16 object-cover rounded-lg border border-outline-variant" />
                <button
                  onClick={() => setAttachedImage(null)}
                  className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-error text-on-error flex items-center justify-center text-xs shadow-sm"
                >
                  <span className="material-symbols-outlined text-[12px]">close</span>
                </button>
              </div>
            )}
            <div className="flex gap-2 items-end">
              <input ref={imageRef} type="file" accept="image/*" className="hidden" onChange={handleImageAttach} />
              <button
                onClick={() => imageRef.current?.click()}
                className="p-3 rounded-xl bg-surface-container-high text-on-surface hover:bg-surface-variant transition-all cursor-pointer border border-outline-variant"
                title="Attach image"
              >
                <span className="material-symbols-outlined">image</span>
              </button>
              
              <button
                onClick={isRecording ? stopRecording : startRecording}
                className={`p-3 rounded-xl transition-all cursor-pointer border border-outline-variant ${
                  isRecording 
                    ? "bg-error/10 text-error border-error/20 animate-pulse" 
                    : "bg-surface-container-high text-on-surface hover:bg-surface-variant"
                }`}
                title={isRecording ? "Stop recording" : "Record voice (Whisper AI)"}
              >
                <span className="material-symbols-outlined">{isRecording ? "stop_circle" : "mic"}</span>
              </button>

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
                disabled={(!input.trim() && !attachedImage) || loading}
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
