"use client";

import { useEffect, useState } from "react";
import { authHelpers, type CurrentUser } from "@/lib/auth";

export default function TopNavBar() {
  const [user, setUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    setUser(authHelpers.getCurrentUser());
  }, []);

  const initials = user?.email?.slice(0, 2).toUpperCase() ?? "??";

  return (
    <header className="fixed top-0 right-0 h-16 w-[calc(100%-260px)] z-40 flex justify-between items-center px-6 glass-nav border-b border-outline-variant">
      {/* Search */}
      <div className="flex items-center flex-1 max-w-xl">
        <div className="relative w-full group focus-within:ring-1 focus-within:ring-primary rounded-lg">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">
            search
          </span>
          <input
            className="w-full bg-surface-container-low border border-outline-variant rounded-lg py-1.5 pl-10 pr-4 text-sm text-on-surface focus:outline-none focus:border-primary placeholder:text-on-surface-variant/50 transition-colors"
            placeholder="Search…"
            type="text"
          />
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">
        {/* Status pill */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-surface-container rounded-full border border-outline-variant">
          <div className="w-2 h-2 rounded-full bg-secondary animate-pulse" />
          <span className="text-xs text-secondary font-medium">System Online</span>
        </div>

        <div className="h-5 w-px bg-outline-variant" />

        {/* User avatar + logout */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-primary-container/40 border border-primary/30 flex items-center justify-center text-xs font-bold text-primary">
            {initials}
          </div>
          {user && (
            <span className="hidden md:block text-xs text-on-surface-variant max-w-[120px] truncate">
              {user.email}
            </span>
          )}
          <button
            onClick={() => authHelpers.logout()}
            title="Sign out"
            className="text-on-surface-variant hover:text-error transition-colors p-1.5 rounded-lg hover:bg-error-container/20 cursor-pointer"
          >
            <span className="material-symbols-outlined text-lg">logout</span>
          </button>
        </div>
      </div>
    </header>
  );
}
