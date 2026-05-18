"use client";

import { useState, useEffect } from "react";
import StatsCard from "@/components/StatsCard";
import { dashboardApi, type DashboardStats, type WorkflowLog } from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [workflowLogs, setWorkflowLogs] = useState<WorkflowLog[]>([]);
  const [aiUsage, setAiUsage] = useState<{ date: string; total_queries: number; rag_hits: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [s, wf, usage] = await Promise.all([
          dashboardApi.stats(),
          dashboardApi.workflowLogs(),
          dashboardApi.aiUsage(),
        ]);
        setStats(s.data);
        setWorkflowLogs(wf.data.slice(0, 8));
        setAiUsage(usage.data.slice(0, 7).reverse());
      } catch {
        // Will show skeleton/empty state
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const maxQueries = Math.max(...aiUsage.map((d) => d.total_queries), 1);

  return (
    <main className="ml-(--spacing-sidebar-width) min-h-screen relative overflow-hidden">
      {/* Premium Background Mesh */}
      <div className="absolute inset-0 z-0 opacity-40 pointer-events-none login-mesh" />
      
      <div className="pt-24 px-6 pb-10 max-w-screen-2xl mx-auto relative z-10">
        {/* Header */}
        <header className="mb-10 flex items-end justify-between glass-nav p-6 rounded-2xl border border-outline-variant/30 shadow-lg">
          <div>
            <p className="text-xs font-bold text-primary uppercase tracking-[0.2em] mb-2 drop-shadow-sm">Workspace Overview</p>
            <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-primary to-inverse-primary tracking-tight">
              Command Center
            </h1>
          </div>
          <div className="text-sm font-medium text-on-surface-variant bg-surface/50 px-4 py-2 rounded-full border border-outline-variant/50 backdrop-blur-md">
            {new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
          </div>
        </header>

        {/* Stats Grid */}
        <section className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-5 mb-10">
          {loading ? (
            Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-32 rounded-2xl bg-surface-container/50 animate-pulse border border-outline-variant/20" />
            ))
          ) : (
            <>
              <StatsCard title="Total Leads" value={stats?.total_leads ?? 0} icon="group" accent="primary" />
              <StatsCard title="Hot Leads" value={stats?.hot_leads ?? 0} icon="local_fire_department" accent="error" />
              <StatsCard title="Conversations" value={stats?.total_conversations ?? 0} icon="forum" accent="secondary" />
              <StatsCard title="Workflows Run" value={stats?.workflows_run ?? 0} icon="play_circle" accent="tertiary" />
              <StatsCard title="Documents" value={stats?.documents_uploaded ?? 0} icon="folder" accent="primary" />
              <StatsCard
                title="Avg Similarity"
                value={`${((stats?.avg_similarity_score ?? 0) * 100).toFixed(1)}%`}
                icon="analytics"
                accent="secondary"
              />
            </>
          )}
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Daily Query Chart */}
          <div className="bg-surface-container/60 backdrop-blur-xl rounded-3xl border border-outline-variant/40 p-6 shadow-xl hover:border-primary/30 transition-colors duration-300">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-on-surface">AI Usage Trends</h2>
              <span className="material-symbols-outlined text-primary/70">monitoring</span>
            </div>
            {aiUsage.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 opacity-50">
                <span className="material-symbols-outlined text-4xl mb-2">bar_chart</span>
                <p className="text-sm text-on-surface-variant">No usage data yet.</p>
              </div>
            ) : (
              <div className="flex items-end gap-3 h-40">
                {aiUsage.map((day) => (
                  <div key={day.date} className="flex-1 flex flex-col items-center gap-2 group">
                    <div
                      className="w-full rounded-t-lg chart-bar min-h-[4px] transition-all duration-500 ease-out opacity-80 group-hover:opacity-100 group-hover:shadow-[0_0_15px_rgba(77,142,255,0.4)]"
                      style={{ height: `${(day.total_queries / maxQueries) * 100}%` }}
                      title={`${day.total_queries} queries`}
                    />
                    <span className="text-[10px] font-medium text-on-surface-variant/70 uppercase">
                      {new Date(day.date).toLocaleDateString("en-US", { weekday: "short" })}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Workflow Logs */}
          <div className="bg-surface-container/60 backdrop-blur-xl rounded-3xl border border-outline-variant/40 p-6 shadow-xl hover:border-secondary/30 transition-colors duration-300">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-on-surface">Recent Automations</h2>
              <span className="material-symbols-outlined text-secondary/70">bolt</span>
            </div>
            {workflowLogs.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 opacity-50">
                <span className="material-symbols-outlined text-4xl mb-2">history</span>
                <p className="text-sm text-on-surface-variant">No workflows run yet.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {workflowLogs.map((log) => (
                  <div key={log.id} className="flex items-center justify-between p-3 rounded-xl bg-surface/40 hover:bg-surface/80 border border-outline-variant/20 transition-all cursor-default">
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center shadow-inner ${
                        log.status === "success" ? "bg-secondary-container/20 text-secondary" : "bg-error-container/20 text-error"
                      }`}>
                        <span className="material-symbols-outlined text-sm">
                          {log.status === "success" ? "check" : "close"}
                        </span>
                      </div>
                      <span className="text-sm font-semibold text-on-surface capitalize tracking-wide">{log.workflow_name.replace(/_/g, " ")}</span>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className="text-xs font-medium text-on-surface-variant bg-surface-container-highest px-2 py-0.5 rounded-full mb-1">{log.duration_ms}ms</span>
                      <span className="text-[10px] text-on-surface-variant/60">
                        {new Date(log.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
