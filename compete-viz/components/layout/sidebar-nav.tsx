"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "@/lib/constants";
import { getCompanyName } from "@/lib/company";
import { useAuth } from "@/components/auth/auth-provider";
import {
  LayoutDashboard,
  Grid3X3,
  ScatterChart,
  Layers,
  ShieldAlert,
  ArrowLeftRight,
  LogOut,
} from "lucide-react";

const icons = {
  LayoutDashboard,
  Grid3X3,
  ScatterChart,
  Layers,
  ShieldAlert,
  ArrowLeftRight,
} as const;

export function SidebarNav() {
  const pathname = usePathname();
  const { logout } = useAuth();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-56 flex-col border-r border-border bg-sidebar">
      <div className="flex h-14 items-center gap-2 border-b border-border px-4">
        <div className="h-7 w-7 rounded-md bg-primary flex items-center justify-center">
          <span className="text-xs font-bold text-primary-foreground">CI</span>
        </div>
        <h1 className="text-sm font-semibold text-foreground">Competitive Intelligence</h1>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {NAV_ITEMS.map((item) => {
          const Icon = icons[item.icon];
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                isActive
                  ? "bg-sidebar-accent text-primary font-medium"
                  : "text-muted-foreground hover:bg-sidebar-accent hover:text-foreground"
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-border p-3 space-y-2">
        <div className="rounded-md bg-accent/10 px-3 py-2">
          <p className="text-[10px] font-medium text-accent">{getCompanyName().toUpperCase()}</p>
          <p className="text-[10px] text-muted-foreground">53 competitors tracked</p>
        </div>
        <button
          onClick={logout}
          className="flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-xs text-muted-foreground hover:bg-sidebar-accent hover:text-foreground transition-colors"
        >
          <LogOut className="h-3 w-3" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
