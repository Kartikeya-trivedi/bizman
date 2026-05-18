"use client";

import { useEffect, useState } from "react";
import { dashboardApi } from "@/lib/api";

interface TraceStep {
  agent: string;
  action: string;
  output: Record<string, unknown>;
}

interface AgentTrace {
  timestamp: string;
  user_id: string;
  conversation_id: string;
  message: string;
  steps: TraceStep[];
  final_answer: string;
}

export default function TracingPage() {
  const [traces, setTraces] = useState<AgentTrace[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi.agentTraces().then((r) => {
      setTraces(r.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  return (
    <main className="ml-(--spacing-sidebar-width) min-h-screen pt-24 px-6 pb-10 max-w-screen-2xl mx-auto">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-on-surface">Agent Tracing</h1>
        <p className="text-sm text-on-surface-variant mt-0.5">
          Step-by-step insight into the AI's reasoning, intent classification, and RAG validation.
        </p>
      </header>

      {loading ? (
        <div className="text-sm text-on-surface-variant animate-pulse">Loading traces...</div>
      ) : traces.length === 0 ? (
        <div className="bg-surface-container rounded-xl border border-outline-variant p-8 text-center">
          <span className="material-symbols-outlined text-4xl text-on-surface-variant/50 mb-3">analytics</span>
          <h3 className="text-on-surface font-medium mb-1">No Traces Yet</h3>
          <p className="text-sm text-on-surface-variant">Send a message in the chat to generate agent traces.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {traces.map((trace, i) => (
            <div key={i} className="bg-surface-container rounded-xl border border-outline-variant overflow-hidden">
              <div className="bg-surface-container-low p-4 border-b border-outline-variant flex justify-between items-center">
                <div>
                  <p className="text-xs text-on-surface-variant font-medium uppercase tracking-wider mb-1">User Prompt</p>
                  <p className="text-sm text-on-surface">"{trace.message}"</p>
                </div>
                <div className="text-right">
                  <span className="text-xs text-on-surface-variant/70">{new Date(trace.timestamp).toLocaleString()}</span>
                  <p className="text-xs text-on-surface-variant font-mono mt-1" title={trace.conversation_id}>
                    ID: {trace.conversation_id.slice(0, 8)}...
                  </p>
                </div>
              </div>

              <div className="p-5 overflow-x-auto">
                <div className="flex gap-4 min-w-max">
                  {trace.steps.map((step, idx) => (
                    <div key={idx} className="w-72 shrink-0 bg-surface border border-outline-variant/50 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-outline-variant/30">
                        <span className={`material-symbols-outlined text-base ${
                          step.agent === "Planner" ? "text-primary" : 
                          step.agent === "Executor" ? "text-secondary" : 
                          "text-tertiary"
                        }`}>
                          {step.agent === "Planner" ? "psychology" : 
                           step.agent === "Executor" ? "build" : 
                           "fact_check"}
                        </span>
                        <div>
                          <h4 className="text-sm font-semibold text-on-surface">{step.agent}</h4>
                          <p className="text-[10px] text-on-surface-variant uppercase">{step.action}</p>
                        </div>
                      </div>
                      
                      <pre className="text-xs text-on-surface-variant whitespace-pre-wrap font-mono bg-surface-container-low p-2 rounded">
                        {JSON.stringify(step.output, null, 2)}
                      </pre>
                    </div>
                  ))}
                  
                  {/* Final Output Node */}
                  <div className="w-80 shrink-0 bg-surface border border-primary/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3 pb-2 border-b border-primary/20">
                      <span className="material-symbols-outlined text-base text-primary">done_all</span>
                      <div>
                        <h4 className="text-sm font-semibold text-on-surface">Final Answer</h4>
                        <p className="text-[10px] text-on-surface-variant uppercase">Streamed to UI</p>
                      </div>
                    </div>
                    <div className="text-xs text-on-surface-variant line-clamp-6">
                      {trace.final_answer}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
