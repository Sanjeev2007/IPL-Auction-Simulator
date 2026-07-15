"use client";

/**
 * Precision Terminal — small shared pieces for the auction screens.
 * Heat-encoded rating cells, a self-ticking countdown bar, and form controls,
 * all styled from the same @theme tokens the dashboard uses.
 */

import { clsx } from "clsx";
import { useEffect, useState, type InputHTMLAttributes, type ReactNode } from "react";
import { heatColor } from "@/lib/design";

/* ── Rating, heat-encoded ────────────────────────────────────────────────── */
export function Rating({
  label,
  value,
  size = "md",
}: {
  label: string;
  value: number;
  size?: "sm" | "md";
}) {
  const color = heatColor(value, 40, 100);
  return (
    <div className="flex flex-col items-center gap-1">
      <span className="font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">{label}</span>
      <span
        className={clsx(
          "font-mono tnum font-semibold leading-none",
          size === "md" ? "text-[22px]" : "text-[15px]"
        )}
        style={{ color }}
      >
        {value.toFixed(0)}
      </span>
    </div>
  );
}

/** Inline heat pip + number, for dense squad rows. */
export function RatingPip({ value }: { value: number }) {
  const color = heatColor(value, 40, 100);
  return (
    <span className="inline-flex items-center gap-[5px]">
      <span className="inline-block h-[7px] w-[7px] rounded-full" style={{ background: color }} aria-hidden />
      <span className="font-mono tnum text-[12.5px]" style={{ color }}>
        {value.toFixed(0)}
      </span>
    </span>
  );
}

/* ── Countdown bar (self-ticking off a deadline) ─────────────────────────── */
export function TimerBar({
  deadlineMs,
  totalSeconds,
}: {
  deadlineMs: number | null;
  totalSeconds: number | null;
}) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!deadlineMs) return;
    const id = setInterval(() => setNow(Date.now()), 100);
    return () => clearInterval(id);
  }, [deadlineMs]);

  const total = totalSeconds && totalSeconds > 0 ? totalSeconds : 30;
  const remainingMs = deadlineMs ? Math.max(0, deadlineMs - now) : total * 1000;
  const secs = Math.ceil(remainingMs / 1000);
  const pct = deadlineMs ? Math.max(0, Math.min(100, (remainingMs / (total * 1000)) * 100)) : 100;
  const urgent = deadlineMs != null && secs <= 5;
  const color = urgent ? "var(--color-hot)" : "var(--color-accent)";

  return (
    <div className="w-full">
      <div className="mb-2 flex items-baseline justify-between">
        <span className="font-mono text-[10.5px] uppercase tracking-[0.1em] text-faint">
          {deadlineMs ? "Time on the clock" : "Waiting"}
        </span>
        <span
          className="font-mono tnum text-[28px] font-semibold leading-none tabular-nums"
          style={{ color }}
        >
          {deadlineMs ? `${secs}s` : "—"}
        </span>
      </div>
      <div className="h-[6px] w-full overflow-hidden rounded-full bg-elevated">
        <div
          className="h-full rounded-full"
          style={{ width: `${pct}%`, background: color, transition: "width 120ms linear" }}
        />
      </div>
    </div>
  );
}

/* ── Form controls ───────────────────────────────────────────────────────── */
export function Field({
  label,
  hint,
  className,
  ...props
}: { label: string; hint?: ReactNode } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="block">
      <span className="mb-[6px] block font-mono text-[10.5px] uppercase tracking-[0.09em] text-faint">
        {label}
      </span>
      <input
        {...props}
        className={clsx(
          "w-full rounded-md border border-edge bg-bg px-3 py-2.5 text-[14px] text-ink outline-none",
          "placeholder:text-faint focus:border-accent/60 focus:ring-1 focus:ring-accent/30",
          props.type === "number" ? "font-mono tnum" : "",
          className
        )}
      />
      {hint && <span className="mt-[5px] block text-[11.5px] text-faint">{hint}</span>}
    </label>
  );
}

export function GhostButton({
  children,
  className,
  ...props
}: { children: ReactNode } & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-md border border-edge bg-elevated px-4 py-2.5 text-[13px] font-medium text-ink",
        "transition-colors hover:border-faint disabled:cursor-not-allowed disabled:opacity-40",
        className
      )}
    >
      {children}
    </button>
  );
}

/* ── Connection dot ──────────────────────────────────────────────────────── */
export function StatusDot({ ok, title }: { ok: boolean; title?: string }) {
  return (
    <span
      title={title}
      className="inline-block h-[7px] w-[7px] rounded-full"
      style={{ background: ok ? "var(--color-accent)" : "var(--color-faint)" }}
      aria-hidden
    />
  );
}
