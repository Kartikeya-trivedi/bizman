"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", icon: "dashboard", label: "Dashboard" },
  { href: "/chat", icon: "forum", label: "Chat" },
  { href: "/leads", icon: "group", label: "Leads" },
  { href: "/workflows", icon: "account_tree", label: "Workflows" },
  { href: "/documents", icon: "description", label: "Documents" },
  { href: "/tracing", icon: "analytics", label: "Tracing" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-sidebar-width bg-surface/80 backdrop-blur-2xl border-r border-outline-variant/30 flex flex-col py-md z-50 shadow-2xl">
      <div className="px-md mb-xl mt-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-inverse-primary flex items-center justify-center shadow-[0_0_20px_rgba(77,142,255,0.4)]">
            <span className="material-symbols-outlined text-on-primary font-bold">psychology</span>
          </div>
          <div>
            <h1 className="font-headline-md text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-fixed to-primary tracking-tight">
              BizMind AI
            </h1>
            <p className="text-[10px] text-on-surface-variant uppercase tracking-[0.2em] mt-0.5 opacity-80 font-bold">
              Command Center
            </p>
          </div>
        </div>
      </div>
      <nav className="flex-1 space-y-1.5 px-3">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer active:scale-95 transition-all duration-300 ${
                isActive
                  ? "bg-primary/10 text-primary border border-primary/20 shadow-[0_0_15px_rgba(77,142,255,0.1)] font-semibold"
                  : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest/50 border border-transparent"
              }`}
            >
              <span
                className={`material-symbols-outlined transition-transform duration-300 ${isActive ? "scale-110" : ""}`}
                style={isActive ? { fontVariationSettings: "'FILL' 1" } : {}}
              >
                {item.icon}
              </span>
              <span className="font-body-md text-sm">{item.label}</span>
            </Link>
          );
        })}
        <div className="pt-4 mt-4 border-t border-outline-variant/30">
          <Link
            href="/settings"
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest/50 cursor-pointer active:scale-95 transition-all duration-300 border border-transparent"
          >
            <span className="material-symbols-outlined">settings</span>
            <span className="font-body-md text-sm">Settings</span>
          </Link>
        </div>
      </nav>
      <div className="mt-auto px-4 pt-4 pb-6">
        <div className="flex items-center gap-3 p-3 rounded-xl bg-surface-container-low/50 border border-outline-variant/30 hover:border-outline-variant hover:bg-surface-container-high/50 transition-all cursor-pointer shadow-sm group">
          <img
            alt="User Administrator Avatar"
            className="w-10 h-10 rounded-full bg-primary-container object-cover border-2 border-primary/20 group-hover:border-primary/50 transition-colors"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuBv21gf60brsdRzri2Qhd6U9QBZx5uW16HmdbyZEXxAVgfsST0GYGQa76B7iCfhCnc8vOG7WvO8sq8G-Rd68KJaZVatvwTZ3OKpsN4brPoj_qVL3JctrY6SKRSpZp_H4sdPGREK6bpT7fyhRx4RWACDw2KsSj8AkhQA157U5xfweIfFGVmTGEN5eEPRpRA7eeVBpn6X9OVAmzVgPtHpmMC2nZlY4gyB-0uYWi7xkUcMgGirNaVPwWltEsrRjgsjH2n98v-Ai_95omI"
          />
          <div className="overflow-hidden">
            <p className="font-label-md text-sm text-on-surface font-bold truncate">
              Admin User
            </p>
            <p className="font-label-md text-[10px] text-primary truncate uppercase tracking-wider font-bold opacity-80">
              Enterprise Account
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
