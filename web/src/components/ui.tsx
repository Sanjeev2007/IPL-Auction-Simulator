/**
 * Precision Terminal — shared, presentational building blocks.
 *
 * These are the "one terminal platform" primitives: the hairline data pane,
 * the page header, the KPI tile, and the table cell classes. Every page composes
 * these so the whole app reads as a single cohesive instrument. Pure/server-safe
 * (no hooks) so both server and client pages can use them; motion lives in
 * `motion.tsx` and data lives in `lib/` — this file only styles.
 */

import { clsx } from "clsx";
import type { ReactNode } from "react";

/* ------------------------------------------------------------------ */
/* Panel — the hairline-bordered "pane"                                */
/* ------------------------------------------------------------------ */

export function Panel({
  title,
  meta,
  right,
  children,
  className,
  bodyClassName,
}: {
  title: ReactNode;
  /** Mono metadata string shown at the right of the header. */
  meta?: ReactNode;
  /** Full custom right-side header content (overrides `meta`). */
  right?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section className={clsx("panel", className)}>
      <div className="panel-head">
        <span className="panel-title">{title}</span>
        {right ?? (meta != null ? <span className="panel-meta">{meta}</span> : null)}
      </div>
      <div className={clsx("panel-body", bodyClassName)}>{children}</div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* PageHead — big display title + subtitle + optional right meta       */
/* ------------------------------------------------------------------ */

export function PageHead({
  title,
  sub,
  metaLabel,
  metaValue,
}: {
  title: ReactNode;
  sub?: ReactNode;
  metaLabel?: ReactNode;
  metaValue?: ReactNode;
}) {
  return (
    <div className="mb-[18px] flex flex-col items-start justify-between gap-4 border-b border-edge-soft pb-[18px] sm:flex-row sm:items-end">
      <div>
        <h1 className="font-display text-[27px] font-semibold leading-none">{title}</h1>
        {sub && <p className="mt-[7px] max-w-2xl text-[13px] leading-relaxed text-muted">{sub}</p>}
      </div>
      {(metaLabel || metaValue) && (
        <div className="shrink-0 text-left sm:text-right">
          <div className="font-mono text-[11px] uppercase tracking-[0.06em] text-faint">
            {metaLabel}
          </div>
          <div className="mt-[3px] font-mono text-[13px] text-muted">{metaValue}</div>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Kpi — a single stat tile in the KPI strip                           */
/* ------------------------------------------------------------------ */

export function Kpi({
  label,
  value,
  foot,
  valueColor,
  className,
}: {
  label: ReactNode;
  value: ReactNode;
  foot?: ReactNode;
  /** heatColor()'d value color for the big number. */
  valueColor?: string;
  className?: string;
}) {
  return (
    <div className={clsx("rounded-md border border-edge bg-surface px-4 py-[14px]", className)}>
      <div className="font-mono text-[10.5px] uppercase tracking-[0.08em] text-faint">{label}</div>
      <div
        className="mt-[6px] font-mono tnum text-[26px] font-medium leading-none tracking-[-0.01em]"
        style={valueColor ? { color: valueColor } : undefined}
      >
        {value}
      </div>
      {foot != null && <div className="mt-[6px] text-[11.5px] text-muted">{foot}</div>}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Empty state — honest "no data / backend offline"                    */
/* ------------------------------------------------------------------ */

export function EmptyState({
  title,
  meta = "NO DATA",
  children,
}: {
  title: ReactNode;
  meta?: ReactNode;
  children: ReactNode;
}) {
  return (
    <Panel title={title} meta={meta} bodyClassName="py-10 text-center text-sm text-muted">
      {children}
    </Panel>
  );
}

/* ------------------------------------------------------------------ */
/* The heat legend ramp (0 → cool·warm·hot → 100)                      */
/* ------------------------------------------------------------------ */

export function HeatRamp({ className }: { className?: string }) {
  return (
    <span
      className={clsx("inline-block h-[5px] w-24 rounded-[3px]", className)}
      style={{
        background:
          "linear-gradient(90deg, var(--color-cool), var(--color-warm), var(--color-hot))",
      }}
      aria-hidden
    />
  );
}

/* ------------------------------------------------------------------ */
/* Shared table cell classes                                           */
/* ------------------------------------------------------------------ */

export const thBase =
  "border-b border-edge px-[10px] pb-[10px] pt-3 text-right font-mono text-[10.5px] font-medium uppercase tracking-[0.09em] text-faint";
export const thL = thBase + " text-left";
export const tdBase = "px-[10px] py-[13px] text-right font-mono tnum text-[14px] text-muted";

/** "Kolkata Knight Riders" full name — only when it differs from the abbr. */
export function fullName(name: string, id: string): string {
  return name && name !== id ? name : "";
}
