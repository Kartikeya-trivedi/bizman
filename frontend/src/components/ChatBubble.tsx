/**
 * BizMind AI — ChatBubble Component
 * Message bubble for user and assistant messages.
 */

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ChatBubbleProps {
  role: "user" | "assistant";
  content: string;
  images?: string[];
  sources?: string[];
  hallucination_flagged?: boolean;
  timestamp?: string;
}

export default function ChatBubble({
  role,
  content,
  images = [],
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
        {/* Images */}
        {images && images.length > 0 && (
          <div className="flex gap-2 flex-wrap mb-1">
            {images.map((img, i) => (
              <img key={i} src={img} alt="Attached" className="max-w-[200px] max-h-[200px] object-cover rounded-lg border border-outline-variant" />
            ))}
          </div>
        )}

        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? "bg-primary text-on-primary rounded-tr-sm whitespace-pre-wrap"
              : "bg-surface-container text-on-surface border border-outline-variant rounded-tl-sm markdown-body"
          }`}
        >
          {isUser ? (
            content
          ) : (
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
                ul: ({node, ...props}) => <ul className="list-disc ml-4 mb-2" {...props} />,
                ol: ({node, ...props}) => <ol className="list-decimal ml-4 mb-2" {...props} />,
                li: ({node, ...props}) => <li className="mb-1" {...props} />,
                h1: ({node, ...props}) => <h1 className="text-xl font-bold mt-3 mb-2" {...props} />,
                h2: ({node, ...props}) => <h2 className="text-lg font-bold mt-3 mb-2" {...props} />,
                h3: ({node, ...props}) => <h3 className="font-bold mt-2 mb-1" {...props} />,
                code: ({node, className, children, ...props}) => {
                  const match = /language-(\w+)/.exec(className || '');
                  return match ? (
                    <pre className="bg-surface-variant text-on-surface p-2 rounded text-xs overflow-x-auto mt-2 mb-2">
                      <code className={className} {...props}>{children}</code>
                    </pre>
                  ) : (
                    <code className="bg-surface-variant text-on-surface px-1 py-0.5 rounded text-xs font-mono" {...props}>{children}</code>
                  )
                },
                strong: ({node, ...props}) => <strong className="font-bold text-primary" {...props} />,
              }}
            >
              {content}
            </ReactMarkdown>
          )}
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
