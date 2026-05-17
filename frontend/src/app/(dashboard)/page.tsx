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
    <main className="ml-(--spacing-sidebar-width) pt-24 px-6 pb-10 max-w-screen-2xl mx-auto min-h-screen">
      {/* Header */}
      <header className="mb-8 flex items-end justify-between">
        <div>
          <p className="text-xs font-medium text-primary uppercase tracking-widest mb-1">Overview</p>
          <h1 className="text-3xl font-bold text-on-surface">Dashboard</h1>
        </div>
        <div className="text-xs text-on-surface-variant">
          {new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
        </div>
      </header>

      {/* Stats Grid */}
      <section className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
        {loading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-28 rounded-xl bg-surface-container animate-pulse" />
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Query Chart */}
        <div className="bg-surface-container rounded-xl border border-outline-variant p-5">
          <h2 className="text-sm font-semibold text-on-surface mb-4">Daily Queries</h2>
          {aiUsage.length === 0 ? (
            <p className="text-xs text-on-surface-variant text-center py-8">No usage data yet.</p>
          ) : (
            <div className="flex items-end gap-2 h-32">
              {aiUsage.map((day) => (
                <div key={day.date} className="flex-1 flex flex-col items-center gap-1">
                  <div
                    className="w-full rounded-t chart-bar min-h-[4px] transition-all"
                    style={{ height: `${(day.total_queries / maxQueries) * 100}%` }}
                    title={`${day.total_queries} queries`}
                  />
                  <span className="text-xs text-on-surface-variant">
                    {new Date(day.date).toLocaleDateString("en-US", { weekday: "short" })}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Workflow Logs */}
        <div className="bg-surface-container rounded-xl border border-outline-variant p-5">
          <h2 className="text-sm font-semibold text-on-surface mb-4">Recent Workflows</h2>
          {workflowLogs.length === 0 ? (
            <p className="text-xs text-on-surface-variant text-center py-8">No workflows run yet.</p>
          ) : (
            <div className="space-y-2">
              {workflowLogs.map((log) => (
                <div key={log.id} className="flex items-center justify-between py-2 border-b border-outline-variant/50 last:border-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-2 h-2 rounded-full shrink-0 ${
                        log.status === "success" ? "bg-secondary" : "bg-error"
                      }`}
                    />
                    <span className="text-xs text-on-surface capitalize">{log.workflow_name.replace(/_/g, " ")}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-on-surface-variant">{log.duration_ms}ms</span>
                    <span className="text-xs text-on-surface-variant/50">
                      {new Date(log.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
