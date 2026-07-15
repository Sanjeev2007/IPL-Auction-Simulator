"use client";

/**
 * Precision Terminal — application shell.
 *
 * Owns the sidebar collapse state and frames every page: fixed left rail
 * (`Sidebar`), a slim sticky top bar (breadcrumb + real engine metadata), and
 * the scrolling content well. Server-rendered data pages are passed through as
 * `children`, so this client boundary never touches data fetching.
 *
 * Responsive: below md the rail is an off-canvas drawer opened from a hamburger
 * in the top bar (with a tap-to-dismiss backdrop); content sits full-width. At
 * md+ the content margin follows the rail width. The drawer auto-closes on
 * navigation.
 *
 * Note: the top bar intentionally carries real metadata rather than a global
 * search box — there is no cross-page searchable entity, and the repo's honesty
 * rules forbid non-functional UI. A real per-table filter can be added later.
 */

import { useEffect, useState, type CSSProperties } from "react";
import { usePathname } from "next/navigation";
import { Menu } from "lucide-react";
import Sidebar, { SIDEBAR_W, SIDEBAR_W_COLLAPSED } from "@/components/Navbar";

const TITLES: { match: (p: string) => boolean; label: string }[] = [
  { match: (p) => p === "/", label: "Overview" },
  { match: (p) => p.startsWith("/simulator"), label: "Simulator" },
  { match: (p) => p.startsWith("/tournament"), label: "Tournament" },
  { match: (p) => p.startsWith("/analytics"), label: "Analytics" },
  { match: (p) => p.startsWith("/auction"), label: "Auction" },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();
  const section = TITLES.find((t) => t.match(pathname))?.label ?? "Overview";

  // Close the mobile drawer whenever the route changes.
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  return (
    <div className="min-h-screen bg-bg">
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed((c) => !c)}
        mobileOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
      />

      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-[1px] md:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden
        />
      )}

      <div
        className="ml-0 flex min-h-screen flex-col transition-[margin] duration-300 ease-out motion-reduce:transition-none md:ml-[var(--sb)]"
        style={{ ["--sb" as keyof CSSProperties]: collapsed ? `${SIDEBAR_W_COLLAPSED}px` : `${SIDEBAR_W}px` } as CSSProperties}
      >
        {/* Slim top bar */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-edge bg-bg/80 px-4 backdrop-blur-md sm:px-6">
          <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.1em]">
            <button
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
              className="-ml-1 mr-1 flex h-8 w-8 items-center justify-center rounded-[6px] text-muted transition-colors hover:bg-nav-active/50 hover:text-ink md:hidden"
            >
              <Menu className="h-[18px] w-[18px]" />
            </button>
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

        <main className="flex-1 px-4 py-5 sm:px-6 sm:py-6 md:px-8 md:py-7">
          <div className="mx-auto w-full max-w-[1440px]">{children}</div>
        </main>
      </div>
    </div>
  );
}
