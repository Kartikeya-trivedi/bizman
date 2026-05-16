/**
 * BizMind AI — Auth Helpers
 * Token stored in both localStorage (for API client) and a cookie (for middleware route protection).
 */
import { authApi, AuthResponse } from "./api";

const TOKEN_KEY = "bizmind_token";
const USER_KEY = "bizmind_user";

export interface CurrentUser {
  user_id: string;
  email: string;
}

/** Write token to a cookie readable by Next.js middleware (not HttpOnly — client-set). */
function setCookie(name: string, value: string, days = 7) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

function deleteCookie(name: string) {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
}

export const authHelpers = {
  register: async (
    email: string,
    password: string,
    fullName: string
  ): Promise<AuthResponse> => {
    const response = await authApi.register(email, password, fullName);
    const data = response.data;
    authHelpers.setSession(data);
    return data;
  },

  login: async (email: string, password: string): Promise<AuthResponse> => {
    const response = await authApi.login(email, password);
    const data = response.data;
    authHelpers.setSession(data);
    return data;
  },

  logout: async (): Promise<void> => {
    try {
      await authApi.logout();
    } catch {
      // Ignore logout errors — always clear locally
    } finally {
      authHelpers.clearSession();
      window.location.href = "/login";
    }
  },

  getCurrentUser: (): CurrentUser | null => {
    if (typeof window === "undefined") return null;
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as CurrentUser;
    } catch {
      return null;
    }
  },

  getToken: (): string | null => {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(TOKEN_KEY);
  },

  isAuthenticated: (): boolean => {
    return !!authHelpers.getToken();
  },

  /** Persist session to localStorage + cookie (cookie read by middleware for SSR route protection). */
  setSession: (data: AuthResponse): void => {
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(
      USER_KEY,
      JSON.stringify({ user_id: data.user_id, email: data.email })
    );
    // Write to cookie so Next.js middleware can gate protected routes
    setCookie(TOKEN_KEY, data.access_token);
  },

  clearSession: (): void => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    deleteCookie(TOKEN_KEY);
  },
};
