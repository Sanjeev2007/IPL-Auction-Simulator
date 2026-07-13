"use client";

/**
 * Precision Terminal — shared motion primitives.
 *
 * Minimal-functional motion (per the design brief): numbers count up, bars fill
 * left→right, panels fade/slide in on data arrival. 150–620ms, ease-out, no bounce.
 * Every primitive respects `prefers-reduced-motion` (renders the final state, no motion).
 *
 * These are the reusable building blocks for all four pages — keep new animation
 * here rather than re-implementing per page.
 */

import { animate, motion, useReducedMotion } from "framer-motion";
import { useEffect, useState, type ReactNode } from "react";

const EASE = [0.22, 0.61, 0.36, 1] as const;

/** Animate a number from 0 → `to` on mount. Renders a plain <span>. */
export function CountUp({
  to,
  decimals = 0,
  duration = 0.78,
  delay = 0,
  className,
  suffix,
}: {
  to: number;
  decimals?: number;
  duration?: number;
  delay?: number;
  className?: string;
  /** Optional unit rendered after the number (e.g. "%"), styled by the caller. */
  suffix?: ReactNode;
}) {
  const reduce = useReducedMotion();
  const [value, setValue] = useState(reduce ? to : 0);

  useEffect(() => {
    if (reduce) {
      setValue(to);
      return;
    }
    const controls = animate(0, to, {
      duration,
      delay,
      ease: EASE,
      onUpdate: setValue,
    });
    return () => controls.stop();
  }, [to, duration, delay, reduce]);

  return (
    <span className={className}>
      {value.toFixed(decimals)}
      {suffix}
    </span>
  );
}

/** Fade + slide a panel/section in on mount. */
export function Reveal({
  children,
  delay = 0,
  className,
  as = "section",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
  as?: "section" | "div";
}) {
  const reduce = useReducedMotion();
  const Comp = as === "div" ? motion.div : motion.section;
  return (
    <Comp
      className={className}
      initial={reduce ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.34, delay, ease: "easeOut" }}
    >
      {children}
    </Comp>
  );
}

/**
 * A hairline heat bar that fills left→right on mount.
 * `pct` is the fill fraction (0–100); `color` is the heat-ramp rgb() string.
 */
export function HeatBar({
  pct,
  color,
  delay = 0,
  height = 8,
  className,
}: {
  pct: number;
  color: string;
  delay?: number;
  height?: number;
  className?: string;
}) {
  const reduce = useReducedMotion();
  return (
    <div
      className={`overflow-hidden rounded-[4px] bg-elevated ${className ?? ""}`}
      style={{ height }}
    >
      <motion.div
        className="h-full origin-left rounded-[4px]"
        style={{ width: `${Math.min(100, Math.max(0, pct))}%`, background: color }}
        initial={reduce ? false : { scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.62, delay, ease: EASE }}
      />
    </div>
  );
}
