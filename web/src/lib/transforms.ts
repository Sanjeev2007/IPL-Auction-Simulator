/**
 * Pure derived-data helpers lifted out of the page components.
 *
 * Keeping these here (a) makes the JSX readable, (b) makes the math unit-testable,
 * and (c) gives Milestone 2's redesign a stable surface to build against.
 */

import type { MatchResult, OverRuns, PointsRow } from "./api";

/**
 * Bar width (as a `%` string) for a value normalized against the largest value
 * in its group — so the leader's bar is full-width and the rest scale down.
 * Was inlined in Home's championship-odds list.
 */
export function normalizeBarWidth(value: number, max: number): string {
  if (!max || max <= 0) return "0%";
  return `${Math.min(100, (value / max) * 100)}%`;
}

/**
 * Playoff probability (%) for a points-table row.
 *
 * Prefers the real `playoff_probability` from the backend when present. Falls
 * back to the original position-based heuristic (top-4 qualify) for the case
 * where the backend has no tournament results yet and every row reads 0.
 * Was inlined in the Tournament table.
 */
export function playoffPct(row: PointsRow, idx: number): number {
  if (row.playoff_probability > 0) {
    return Math.round(row.playoff_probability);
  }
  const isQualifier = idx < 4;
  return isQualifier
    ? Math.round(70 + (4 - idx) * 7)
    : Math.round(Math.max(0, 30 - idx * 4));
}

/** A charts row keyed by the two team names plus an `over` label. */
export type OverSeries = { over: string } & Record<string, number | string>;

function runsInOver(series: OverRuns[] | undefined, over: number): number {
  return series?.find((o) => o.over === over)?.runs ?? 0;
}

function maxOvers(match: MatchResult): number {
  return Math.max(
    match.innings1?.run_rate_by_over?.length ?? 0,
    match.innings2?.run_rate_by_over?.length ?? 0
  );
}

/**
 * Manhattan chart data: runs scored in each over, per team.
 * Was inlined in the Analytics page.
 */
export function buildManhattanData(
  match: MatchResult,
  team1: string,
  team2: string
): OverSeries[] {
  const overs = maxOvers(match);
  return Array.from({ length: overs }, (_, i) => {
    const over = i + 1;
    return {
      over: `Ov ${over}`,
      [team1]: runsInOver(match.innings1?.run_rate_by_over, over),
      [team2]: runsInOver(match.innings2?.run_rate_by_over, over),
    };
  });
}

/**
 * Worm chart data: cumulative runs after each over, per team.
 * Was inlined in the Analytics page.
 */
export function buildWormData(
  match: MatchResult,
  team1: string,
  team2: string
): OverSeries[] {
  const overs = maxOvers(match);
  let c1 = 0;
  let c2 = 0;
  return Array.from({ length: overs }, (_, i) => {
    const over = i + 1;
    c1 += runsInOver(match.innings1?.run_rate_by_over, over);
    c2 += runsInOver(match.innings2?.run_rate_by_over, over);
    return { over: `Ov ${over}`, [team1]: c1, [team2]: c2 };
  });
}
