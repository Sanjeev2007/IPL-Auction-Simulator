"use client";

/**
 * Precision Terminal — application shell.
 *
 * Owns the sidebar collapse state and frames every page: fixed left rail
 * (`Sidebar`), a slim sticky top bar (breadcrumb + real engine metadata), and
 * the scrolling content well. Server-rendered data pages are passed through as
 * `children`, so this client boundary never touches data fetching.
 *
 * Note: the top bar intentionally carries real metadata rather than a global
 * search box — there is no cross-page searchable entity, and the repo's honesty
 * rules forbid non-functional UI. A real per-table filter can be added later.
 */

import { useState } from "react";
import { usePathname } from "next/navigation";
import Sidebar, { SIDEBAR_W, SIDEBAR_W_COLLAPSED } from "@/components/Navbar";

const TITLES: { match: (p: string) => boolean; label: string }[] = [
  { match: (p) => p === "/", label: "Overview" },
  { match: (p) => p.startsWith("/simulator"), label: "Simulator" },
  { match: (p) => p.startsWith("/tournament"), label: "Tournament" },
  { match: (p) => p.startsWith("/analytics"), label: "Analytics" },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();
  const section = TITLES.find((t) => t.match(pathname))?.label ?? "Overview";

  return (
    <div className="min-h-screen bg-bg">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />

      <div
        className="flex min-h-screen flex-col transition-[margin] duration-300 ease-out"
        style={{ marginLeft: collapsed ? SIDEBAR_W_COLLAPSED : SIDEBAR_W }}
      >
        {/* Slim top bar */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-edge bg-bg/80 px-6 backdrop-blur-md">
          <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.1em]">
            <span className="text-faint">IPLSIM</span>
            <span className="text-edge">/</span>
            <span className="text-muted">{section}</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-2 font-mono text-[11px] text-faint sm:flex">
              <span className="inline-block h-[6px] w-[6px] rounded-full bg-accent" aria-hidden />
              ball-by-ball engine
            </span>
            <span className="font-mono text-[11px] tracking-[0.04em] text-faint">v0.2</span>
          </div>
        </header>

        <main className="flex-1 px-6 py-6 md:px-8 md:py-7">
          <div className="mx-auto w-full max-w-[1440px]">{children}</div>
        </main>
      </div>
    </div>
  );
}
