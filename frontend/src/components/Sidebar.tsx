"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", icon: "dashboard", label: "Dashboard" },
  { href: "/chat", icon: "forum", label: "Chat" },
  { href: "/leads", icon: "group", label: "Leads" },
  { href: "/workflows", icon: "account_tree", label: "Workflows" },
  { href: "/documents", icon: "description", label: "Documents" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-sidebar-width bg-surface border-r border-outline-variant flex flex-col py-md z-50">
      <div className="px-md mb-xl">
        <h1 className="font-headline-md text-headline-md font-bold text-primary tracking-tight">
          BizMind AI
        </h1>
        <p className="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mt-1 opacity-60">
          Command Center
        </p>
      </div>
      <nav className="flex-1 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 cursor-pointer active:scale-95 transition-colors duration-200 ${
                isActive
                  ? "bg-surface-container-high text-primary border-l-2 border-primary font-semibold"
                  : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest"
              }`}
            >
              <span
                className="material-symbols-outlined"
                style={isActive ? { fontVariationSettings: "'FILL' 1" } : {}}
              >
                {item.icon}
              </span>
              <span className="font-body-md text-body-md">{item.label}</span>
            </Link>
          );
        })}
        <Link
          href="/login"
          className="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest cursor-pointer active:scale-95 transition-colors duration-200"
        >
          <span className="material-symbols-outlined">settings</span>
          <span className="font-body-md text-body-md">Settings</span>
        </Link>
      </nav>
      <div className="mt-auto px-md pt-md border-t border-outline-variant">
        <div className="flex items-center gap-3 p-2 rounded-lg bg-surface-container-low hover:bg-surface-container transition-colors cursor-pointer">
          {/* Using a standard img tag for simplicity, matching the HTML */}
          <img
            alt="User Administrator Avatar"
            className="w-8 h-8 rounded-full bg-primary-container object-cover"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuBv21gf60brsdRzri2Qhd6U9QBZx5uW16HmdbyZEXxAVgfsST0GYGQa76B7iCfhCnc8vOG7WvO8sq8G-Rd68KJaZVatvwTZ3OKpsN4brPoj_qVL3JctrY6SKRSpZp_H4sdPGREK6bpT7fyhRx4RWACDw2KsSj8AkhQA157U5xfweIfFGVmTGEN5eEPRpRA7eeVBpn6X9OVAmzVgPtHpmMC2nZlY4gyB-0uYWi7xkUcMgGirNaVPwWltEsrRjgsjH2n98v-Ai_95omI"
          />
          <div className="overflow-hidden">
            <p className="font-label-md text-label-md text-on-surface font-bold truncate">
              Admin User
            </p>
            <p className="font-label-md text-[10px] text-on-surface-variant truncate">
              Enterprise Account
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
