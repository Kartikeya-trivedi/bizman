"use client";

import { useState, useEffect } from "react";
import LeadBadge from "@/components/LeadBadge";
import { leadsApi, type Lead } from "@/lib/api";

const STATUSES = ["all", "hot", "warm", "cold"] as const;

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState<string | null>(null);

  const fetchLeads = async (status?: string) => {
    setLoading(true);
    try {
      const resp = await leadsApi.list(status === "all" ? undefined : status);
      setLeads(resp.data);
    } catch {
      setError("Failed to load leads.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeads(filter);
  }, [filter]);

  const updateStatus = async (id: string, status: Lead["status"]) => {
    setUpdating(id);
    try {
      const resp = await leadsApi.update(id, { status });
      setLeads((prev) => prev.map((l) => (l.id === id ? resp.data : l)));
    } catch {
      setError("Failed to update lead.");
    } finally {
      setUpdating(null);
    }
  };

  return (
    <main className="pt-16 ml-[260px] min-h-screen">
      <div className="p-6 max-w-[1440px] mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-on-surface">Leads</h1>
            <p className="text-sm text-on-surface-variant mt-0.5">
              {leads.length} lead{leads.length !== 1 ? "s" : ""} found
            </p>
          </div>
          {/* Filter Tabs */}
          <div className="flex gap-1 p-1 bg-surface-container rounded-lg">
            {STATUSES.map((s) => (
              <button
                key={s}
                onClick={() => setFilter(s)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium capitalize transition-colors cursor-pointer ${
                  filter === s
                    ? "bg-primary text-on-primary"
                    : "text-on-surface-variant hover:text-on-surface"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <p className="text-sm text-error bg-error-container/20 border border-error/30 rounded-lg px-4 py-2 mb-4">
            {error}
          </p>
        )}

        {/* Table */}
        <div className="bg-surface-container rounded-xl border border-outline-variant overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-outline-variant bg-surface-container-low">
                <th className="text-left px-4 py-3 text-xs font-medium text-on-surface-variant">Name</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-on-surface-variant">Email</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-on-surface-variant">Company</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-on-surface-variant">Need</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-on-surface-variant">Status</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-on-surface-variant">Date</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-on-surface-variant">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-on-surface-variant text-xs">
                    Loading…
                  </td>
                </tr>
              )}
              {!loading && leads.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-on-surface-variant text-xs">
                    No leads found. Start a chat conversation to capture leads automatically.
                  </td>
                </tr>
              )}
              {leads.map((lead) => (
                <tr
                  key={lead.id}
                  className="border-b border-outline-variant/50 hover:bg-surface-container-high transition-colors"
                >
                  <td className="px-4 py-3 font-medium text-on-surface">{lead.name}</td>
                  <td className="px-4 py-3 text-on-surface-variant">{lead.email || "—"}</td>
                  <td className="px-4 py-3 text-on-surface-variant">{lead.company || "—"}</td>
                  <td className="px-4 py-3 text-on-surface-variant max-w-[200px] truncate">{lead.need || "—"}</td>
                  <td className="px-4 py-3">
                    <LeadBadge status={lead.status as "hot" | "warm" | "cold"} />
                  </td>
                  <td className="px-4 py-3 text-on-surface-variant text-xs">
                    {new Date(lead.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      {(["hot", "warm", "cold"] as const).filter((s) => s !== lead.status).map((s) => (
                        <button
                          key={s}
                          onClick={() => updateStatus(lead.id, s)}
                          disabled={updating === lead.id}
                          className="text-xs px-2 py-0.5 rounded border border-outline-variant text-on-surface-variant hover:border-primary hover:text-primary transition-colors cursor-pointer disabled:opacity-50"
                        >
                          → {s}
                        </button>
                      ))}
                    </div>
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
