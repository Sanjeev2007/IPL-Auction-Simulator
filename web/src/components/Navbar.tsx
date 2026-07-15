"use client";

/**
 * Precision Terminal — the left rail.
 *
 * Structural port of the v0 sales-ops dashboard sidebar, restyled to the
 * Precision Terminal system (surface panel lifted off pure black, hairline
 * right edge, teal only on the active item). Adapted to Next's real routes:
 * active state comes from `usePathname`, navigation uses `<Link>` — so the data
 * pages stay server components. Collapse state is owned by `AppShell`.
 *
 * Responsive: on ≥md it's a fixed rail whose width follows `collapsed`. Below md
 * it becomes an off-canvas drawer (full 232px), slid in by `mobileOpen` and
 * dismissed by tapping a nav item, the backdrop, or the close button.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import {
  LayoutDashboard,
  Swords,
  Trophy,
  BarChart3,
  Gavel,
  ChevronsLeft,
  ChevronsRight,
  X,
  type LucideIcon,
} from "lucide-react";

export const SIDEBAR_W = 232;
export const SIDEBAR_W_COLLAPSED = 64;

const navItems: { href: string; label: string; icon: LucideIcon }[] = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/simulator", label: "Simulator", icon: Swords },
  { href: "/tournament", label: "Tournament", icon: Trophy },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/auction", label: "Auction", icon: Gavel },
];

export default function Sidebar({
  collapsed,
  onToggle,
  mobileOpen,
  onClose,
}: {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onClose: () => void;
}) {
  const pathname = usePathname();

  return (
    <aside
      className={clsx(
        "fixed left-0 top-0 z-50 flex h-screen w-[232px] flex-col border-r border-edge bg-surface",
        "transition-transform duration-300 ease-out motion-reduce:transition-none",
        "md:z-40 md:w-[var(--sbw)] md:translate-x-0 md:transition-[width]",
        mobileOpen ? "translate-x-0" : "-translate-x-full"
      )}
      style={{ ["--sbw" as string]: collapsed ? `${SIDEBAR_W_COLLAPSED}px` : `${SIDEBAR_W}px` }}
    >
      {/* Wordmark */}
      <div className="flex h-16 items-center gap-3 border-b border-edge px-[18px]">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[6px] border border-edge bg-elevated font-display text-[15px] font-bold leading-none text-accent">
          S
        </div>
        <Link
          href="/"
          className={clsx(
            "font-display text-[18px] font-bold tracking-tight whitespace-nowrap transition-opacity duration-200",
            collapsed && "md:pointer-events-none md:opacity-0"
          )}
        >
          IPL<span className="text-accent">SIM</span>
        </Link>
        {/* Mobile-only close */}
        <button
          onClick={onClose}
          aria-label="Close menu"
          className="ml-auto flex h-8 w-8 items-center justify-center rounded-[6px] text-faint transition-colors hover:bg-nav-active/50 hover:text-muted md:hidden"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-1 overflow-hidden px-3 py-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onClose}
              title={collapsed ? item.label : undefined}
              aria-current={isActive ? "page" : undefined}
              className={clsx(
                "group relative flex items-center gap-3 rounded-[6px] px-3 py-2.5 text-[13px] font-medium transition-colors duration-150",
                isActive
                  ? "bg-nav-active text-ink"
                  : "text-muted hover:bg-nav-active/50 hover:text-ink"
              )}
            >
              {/* Active teal tick */}
              <span
                className={clsx(
                  "absolute left-0 top-1/2 h-5 w-[2px] -translate-y-1/2 rounded-r-full bg-accent transition-opacity duration-200",
                  isActive ? "opacity-100" : "opacity-0"
                )}
                aria-hidden
              />
              <Icon
                className={clsx(
                  "h-[18px] w-[18px] shrink-0 transition-colors",
                  isActive ? "text-accent" : "text-faint group-hover:text-muted"
                )}
              />
              <span
                className={clsx(
                  "whitespace-nowrap transition-opacity duration-200",
                  collapsed && "md:pointer-events-none md:opacity-0"
                )}
              >
                {item.label}
              </span>
            </Link>
          );
        })}
      </nav>

      {/* Footer: version + collapse toggle (desktop only) */}
      <div className="hidden border-t border-edge p-3 md:block">
        <div
          className={clsx(
            "mb-2 px-2 font-mono text-[10px] leading-tight tracking-[0.04em] text-faint transition-opacity duration-200",
            collapsed && "hidden"
          )}
        >
          v0.2 · precision-terminal
        </div>
        <button
          onClick={onToggle}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="flex w-full items-center justify-center gap-2 rounded-[6px] px-3 py-2 text-[12px] text-faint transition-colors hover:bg-nav-active/50 hover:text-muted"
        >
          {collapsed ? (
            <ChevronsRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronsLeft className="h-4 w-4" />
              <span>Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
