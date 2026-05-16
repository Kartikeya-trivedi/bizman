/**
 * BizMind AI — Axios API Client
 * Centralized HTTP client pointing to the FastAPI backend.
 * Auto-injects JWT from localStorage on every request.
 */
import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// ── Request interceptor: attach JWT ────────────────────────────────────────
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("bizmind_token");
      if (token && config.headers) {
        config.headers["Authorization"] = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response interceptor: handle 401 ─────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("bizmind_token");
        localStorage.removeItem("bizmind_user");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// ── Typed API helpers ─────────────────────────────────────────────────────

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
}

export interface ChatResponse {
  answer: string;
  intent: string;
  sources: string[];
  similarity_scores: number[];
  conversation_id: string;
  hallucination_flagged: boolean;
}

export interface Lead {
  id: string;
  user_id: string;
  name: string;
  email: string | null;
  company: string | null;
  need: string | null;
  status: "hot" | "warm" | "cold";
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  user_id: string;
  filename: string;
  created_at: string;
  chunk_count: number;
}

export interface DashboardStats {
  total_leads: number;
  hot_leads: number;
  total_conversations: number;
  workflows_run: number;
  documents_uploaded: number;
  avg_similarity_score: number;
}

export interface WorkflowLog {
  id: string;
  workflow_name: string;
  status: string;
  duration_ms: number;
  created_at: string;
}

export interface EmailSummaryResponse {
  subject: string;
  key_points: string[];
  action_items: string[];
  priority: string;
}

// ── API call functions ────────────────────────────────────────────────────

export const authApi = {
  register: (email: string, password: string, full_name: string) =>
    api.post<AuthResponse>("/auth/register", { email, password, full_name }),
  login: (email: string, password: string) =>
    api.post<AuthResponse>("/auth/login", { email, password }),
  logout: () => api.post("/auth/logout"),
};

export const chatApi = {
  send: (message: string, conversation_id?: string, session_id?: string) =>
    api.post<ChatResponse>("/chat", { message, conversation_id, session_id }),
};

export const leadsApi = {
  list: (status?: string) =>
    api.get<Lead[]>("/leads", { params: status ? { status } : {} }),
  create: (data: Partial<Lead>) => api.post<Lead>("/leads", data),
  update: (id: string, data: Partial<Lead>) =>
    api.patch<Lead>(`/leads/${id}`, data),
};

export const ragApi = {
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  list: () => api.get<Document[]>("/documents"),
  delete: (id: string) => api.delete(`/documents/${id}`),
};

export const dashboardApi = {
  stats: () => api.get<DashboardStats>("/dashboard/stats"),
  conversationLogs: () => api.get("/dashboard/conversation-logs"),
  workflowLogs: () => api.get<WorkflowLog[]>("/dashboard/workflow-logs"),
  aiUsage: () => api.get("/dashboard/ai-usage"),
};

export const workflowsApi = {
  emailSummary: (text: string) =>
    api.post<EmailSummaryResponse>("/workflows/email-summary", { text }),
  leadNotify: (lead_id: string) =>
    api.post("/workflows/lead-notify", { lead_id }),
  crmExport: () => api.post("/workflows/crm-export"),
};
