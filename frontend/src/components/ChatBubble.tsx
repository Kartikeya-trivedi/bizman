/**
 * BizMind AI — ChatBubble Component
 * Message bubble for user and assistant messages.
 */

interface ChatBubbleProps {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  hallucination_flagged?: boolean;
  timestamp?: string;
}

export default function ChatBubble({
  role,
  content,
  sources = [],
  hallucination_flagged = false,
  timestamp,
}: ChatBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"} mb-4`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${
          isUser
            ? "bg-primary text-on-primary"
            : "bg-surface-container-high text-secondary"
        }`}
      >
        {isUser ? (
          <span className="material-symbols-outlined text-base">person</span>
        ) : (
          <span className="material-symbols-outlined text-base">smart_toy</span>
        )}
      </div>

      {/* Bubble */}
      <div className={`max-w-[75%] flex flex-col gap-1 ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? "bg-primary text-on-primary rounded-tr-sm"
              : "bg-surface-container text-on-surface border border-outline-variant rounded-tl-sm"
          }`}
        >
          {content}
        </div>

        {/* Sources */}
        {!isUser && sources.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-1">
            {sources.map((src, i) => (
              <span
                key={i}
                className="text-xs px-2 py-0.5 rounded-full bg-secondary-container/20 text-secondary border border-secondary/20 flex items-center gap-1"
              >
                <span className="material-symbols-outlined text-xs">description</span>
                {src}
              </span>
            ))}
          </div>
        )}

        {/* Hallucination warning */}
        {hallucination_flagged && (
          <div className="flex items-center gap-1.5 text-xs text-tertiary mt-1">
            <span className="material-symbols-outlined text-xs">warning</span>
            <span>Some claims may not be fully verified against documents.</span>
          </div>
        )}

        {/* Timestamp */}
        {timestamp && (
          <span className="text-xs text-on-surface-variant/50 mt-0.5">
            {new Date(timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        )}
      </div>
    </div>
  );
}
