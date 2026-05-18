"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authHelpers } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      if (mode === "login") {
        await authHelpers.login(email, password);
        router.push("/");
      } else {
        const res = await authHelpers.register(email, password, fullName);
        if (!res.access_token) {
          setSuccess("Account created successfully! Please check your email to verify your account before signing in.");
          setMode("login");
        } else {
          router.push("/");
        }
      }
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "An error occurred. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col login-mesh selection:bg-primary-container selection:text-on-primary-container">
      <main className="flex-grow flex items-center justify-center p-4 w-full">
        <div className="w-full max-w-sm">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary-container mb-4">
              <span className="material-symbols-outlined text-2xl text-on-primary-container">psychology</span>
            </div>
            <h1 className="text-2xl font-bold text-on-surface">BizMind AI</h1>
            <p className="text-sm text-on-surface-variant mt-1">
              {mode === "login" ? "Sign in to your workspace" : "Create your workspace"}
            </p>
          </div>

          {/* Card */}
          <div className="bg-surface-container rounded-2xl border border-outline-variant p-6">
            {/* Tabs */}
            <div className="flex rounded-lg bg-surface-container-low p-1 mb-6 gap-1">
              <button
                onClick={() => { setMode("login"); setError(null); setSuccess(null); }}
                className={`flex-1 py-1.5 rounded-md text-sm font-medium transition-colors cursor-pointer ${
                  mode === "login"
                    ? "bg-primary text-on-primary shadow"
                    : "text-on-surface-variant hover:text-on-surface"
                }`}
              >
                Sign In
              </button>
              <button
                onClick={() => { setMode("register"); setError(null); setSuccess(null); }}
                className={`flex-1 py-1.5 rounded-md text-sm font-medium transition-colors cursor-pointer ${
                  mode === "register"
                    ? "bg-primary text-on-primary shadow"
                    : "text-on-surface-variant hover:text-on-surface"
                }`}
              >
                Register
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === "register" && (
                <div>
                  <label className="block text-xs font-medium text-on-surface-variant mb-1.5">Full Name</label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                    placeholder="Jane Smith"
                    className="w-full px-3 py-2.5 rounded-lg bg-surface-container-low border border-outline-variant text-on-surface text-sm placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-colors"
                  />
                </div>
              )}
              <div>
                <label className="block text-xs font-medium text-on-surface-variant mb-1.5">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="you@company.com"
                  className="w-full px-3 py-2.5 rounded-lg bg-surface-container-low border border-outline-variant text-on-surface text-sm placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-colors"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-on-surface-variant mb-1.5">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  placeholder="••••••••"
                  className="w-full px-3 py-2.5 rounded-lg bg-surface-container-low border border-outline-variant text-on-surface text-sm placeholder:text-on-surface-variant/50 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-colors"
                />
              </div>

              {success && (
                <p className="text-xs text-primary bg-primary-container/20 border border-primary/30 rounded-lg px-3 py-2">
                  {success}
                </p>
              )}
              {error && (
                <p className="text-xs text-error bg-error-container/20 border border-error/30 rounded-lg px-3 py-2">
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 rounded-lg bg-primary text-on-primary text-sm font-medium hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-50 cursor-pointer"
              >
                {loading ? "Please wait…" : mode === "login" ? "Sign In" : "Create Account"}
              </button>
            </form>
          </div>

          <p className="text-center text-xs text-on-surface-variant mt-4">
            By signing in, you agree to our{" "}
            <Link href="#" className="text-primary hover:underline">Terms of Service</Link>
          </p>
        </div>
      </main>
    </div>
  );
}
