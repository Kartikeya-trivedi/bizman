"use client";

import { useState, useEffect } from "react";
import { workflowsApi, dashboardApi, type WorkflowLog } from "@/lib/api";

interface WorkflowResult {
  name: string;
  data: Record<string, unknown> | null;
}

export default function WorkflowsPage() {
  const [emailText, setEmailText] = useState("");
  const [leadId, setLeadId] = useState("");
  const [running, setRunning] = useState<string | null>(null);
  const [result, setResult] = useState<WorkflowResult | null>(null);
  const [logs, setLogs] = useState<WorkflowLog[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    dashboardApi.workflowLogs().then((r) => setLogs(r.data)).catch(() => {});
  }, []);

  const runWorkflow = async (name: string, fn: () => Promise<{ data: unknown }>) => {
    setRunning(name);
    setResult(null);
    setError(null);
    try {
      const resp = await fn();
      setResult({ name, data: resp.data as Record<string, unknown> });
      // Refresh logs
      const logsResp = await dashboardApi.workflowLogs();
      setLogs(logsResp.data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Workflow failed.";
      setError(msg);
    } finally {
      setRunning(null);
    }
  };

  return (
    <main className="ml-(--spacing-sidebar-width) min-h-screen">
      <div className="pt-24 px-6 pb-10 max-w-screen-2xl mx-auto">
        <header className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-on-surface">Workflows</h1>
            <p className="text-sm text-on-surface-variant mt-0.5">Trigger AI-powered business workflows.</p>
          </div>
          <button
            onClick={() => window.location.href = "/workflows/builder"}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-on-primary text-sm font-medium hover:opacity-90 transition-all cursor-pointer"
          >
            <span className="material-symbols-outlined text-sm">dashboard_customize</span>
            Visual Builder
          </button>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Email Summarizer */}
          <div className="bg-surface-container rounded-xl border border-outline-variant p-5 col-span-1 lg:col-span-2">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-primary-container/20 flex items-center justify-center">
                <span className="material-symbols-outlined text-xl text-primary">mail</span>
              </div>
              <div>
                <h2 className="text-sm font-semibold text-on-surface">Email Summarizer</h2>
                <p className="text-xs text-on-surface-variant">Extract key points and action items from email text.</p>
              </div>
            </div>
            <textarea
              value={emailText}
              onChange={(e) => setEmailText(e.target.value)}
              placeholder="Paste raw email content here…"
              rows={5}
              className="w-full px-3 py-2.5 rounded-lg bg-surface-container-low border border-outline-variant text-on-surface text-sm placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary transition-colors resize-none mb-3"
            />
            <button
              onClick={() => runWorkflow("Email Summary", () => workflowsApi.emailSummary(emailText))}
              disabled={running !== null || !emailText.trim()}
              className="px-4 py-2 rounded-lg bg-primary text-on-primary text-sm font-medium hover:opacity-90 transition-all disabled:opacity-50 cursor-pointer"
            >
              {running === "Email Summary" ? "Summarizing…" : "Summarize Email"}
            </button>
          </div>

          {/* Quick Workflows */}
          <div className="space-y-4">
            {/* Lead Notify */}
            <div className="bg-surface-container rounded-xl border border-outline-variant p-5">
              <div className="flex items-center gap-2 mb-3">
                <span className="material-symbols-outlined text-xl text-secondary">notifications</span>
                <div>
                  <h3 className="text-sm font-semibold text-on-surface">Lead Notifier</h3>
                  <p className="text-xs text-on-surface-variant">Log a hot lead event.</p>
                </div>
              </div>
              <input
                value={leadId}
                onChange={(e) => setLeadId(e.target.value)}
                placeholder="Lead UUID"
                className="w-full px-3 py-2 rounded-lg bg-surface-container-low border border-outline-variant text-on-surface text-xs placeholder:text-on-surface-variant/50 focus:outline-none focus:border-secondary transition-colors mb-2"
              />
              <button
                onClick={() => runWorkflow("Lead Notify", () => workflowsApi.leadNotify(leadId))}
                disabled={running !== null || !leadId.trim()}
                className="w-full px-3 py-2 rounded-lg bg-secondary-container/30 text-secondary text-xs font-medium hover:bg-secondary-container/50 transition-colors cursor-pointer disabled:opacity-50"
              >
                {running === "Lead Notify" ? "Notifying…" : "Notify Lead"}
              </button>
            </div>

            {/* CRM Export */}
            <div className="bg-surface-container rounded-xl border border-outline-variant p-5">
              <div className="flex items-center gap-2 mb-3">
                <span className="material-symbols-outlined text-xl text-tertiary">download</span>
                <div>
                  <h3 className="text-sm font-semibold text-on-surface">CRM Export</h3>
                  <p className="text-xs text-on-surface-variant">Export all leads to JSON.</p>
                </div>
              </div>
              <button
                onClick={() => runWorkflow("CRM Export", () => workflowsApi.crmExport())}
                disabled={running !== null}
                className="w-full px-3 py-2 rounded-lg bg-tertiary-container/20 text-tertiary text-xs font-medium hover:bg-tertiary-container/40 transition-colors cursor-pointer disabled:opacity-50"
              >
                {running === "CRM Export" ? "Exporting…" : "Export Leads"}
              </button>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="text-sm text-error bg-error-container/20 border border-error/30 rounded-lg px-4 py-3 mb-6">
            {error}
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="bg-surface-container rounded-xl border border-secondary/30 p-5 mb-8">
            <h3 className="text-sm font-semibold text-secondary mb-3">{result.name} — Result</h3>
            <pre className="text-xs text-on-surface-variant overflow-x-auto whitespace-pre-wrap">
              {JSON.stringify(result.data, null, 2)}
            </pre>
          </div>
        )}

        {/* Logs Table */}
        <h2 className="text-sm font-semibold text-on-surface mb-3">Workflow History</h2>
        <div className="bg-surface-container rounded-xl border border-outline-variant overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-outline-variant bg-surface-container-low">
                <th className="text-left px-4 py-3 text-xs font-medium text-on-surface-variant">Workflow</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-on-surface-variant">Status</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-on-surface-variant">Duration</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-on-surface-variant">Time</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-xs text-on-surface-variant">
                    No workflow runs yet.
                  </td>
                </tr>
              )}
              {logs.map((log) => (
                <tr key={log.id} className="border-b border-outline-variant/50 hover:bg-surface-container-high transition-colors">
                  <td className="px-4 py-3 text-on-surface capitalize">{log.workflow_name.replace(/_/g, " ")}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full ${
                      log.status === "success"
                        ? "bg-secondary/15 text-secondary"
                        : "bg-error/15 text-error"
                    }`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${log.status === "success" ? "bg-secondary" : "bg-error"}`} />
                      {log.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-on-surface-variant text-xs">{log.duration_ms}ms</td>
                  <td className="px-4 py-3 text-on-surface-variant text-xs">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}
