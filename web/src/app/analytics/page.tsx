"use client";

/**
 * Match Analytics — per-over breakdown of a single simulated fixture.
 *
 * Precision Terminal port of design/comps/analytics.html. Real data: one
 * `simulateRandomMatch` on load (re-simulate on demand), fed through the pure
 * `buildManhattanData` / `buildWormData` transforms. Charts get the same care as
 * type: hairline grid, mono ticks, teal vs cool series, emphasized endpoints.
 */

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { RefreshCw } from "lucide-react";
import { simulateRandomMatch, type Innings, type MatchResult } from "@/lib/api";
import { buildManhattanData, buildWormData } from "@/lib/transforms";
import { CountUp } from "@/components/motion";
import { EmptyState, Kpi, PageHead, Panel } from "@/components/ui";

const TEAL = "#33E1C6"; // accent — innings 1
const COOL = "#5B8DEF"; // heat cool — innings 2
const EDGE = "#20252F";
const FAINT = "#5A6373";
const SURFACE = "#0A0C10";

function runRate(inn: Innings | null): string {
  if (!inn) return "—";
  const overs = parseFloat(String(inn.overs_completed)) || 0;
  return overs > 0 ? (inn.score / overs).toFixed(2) : "0.00";
}

function topOver(match: MatchResult): { runs: number; team: string; over: number } {
  let best = { runs: 0, team: "", over: 0 };
  for (const inn of [match.innings1, match.innings2]) {
    if (!inn) continue;
    for (const o of inn.run_rate_by_over) {
      if (o.runs > best.runs) best = { runs: o.runs, team: inn.batting_team, over: o.over };
    }
  }
  return best;
}

export default function AnalyticsPage() {
  const [data, setData] = useState<MatchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const run = async () => {
    setLoading(true);
    setError("");
    try {
      setData(await simulateRandomMatch());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    run();
  }, []);

  if (!loading && (error || !data?.innings1 || !data?.innings2)) {
    return (
      <EmptyState title="Match Analytics" meta={error ? "ERROR" : "NO DATA"}>
        {error || "No match data yet. Start the API server and re-simulate."}
      </EmptyState>
    );
  }

  const ready = !loading && data?.innings1 && data?.innings2;
  const team1 = data?.match_info.team1 ?? "";
  const team2 = data?.match_info.team2 ?? "";
  const manhattan = ready ? buildManhattanData(data!, team1, team2) : [];
  const worm = ready ? buildWormData(data!, team1, team2) : [];
  const best = ready ? topOver(data!) : null;

  return (
    <div>
      <PageHead
        title="Match Analytics"
        sub={
          ready
            ? `Per-over breakdown of a simulated fixture · ${data!.innings1!.batting_team} vs ${data!.innings2!.batting_team}`
            : "Per-over breakdown of a simulated fixture."
        }
        metaLabel="Source"
        metaValue="single sim · per over"
      />

      {/* Summary strip */}
      <div className="mb-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {ready ? (
          <>
            <Kpi
              label="Result"
              value={<span className="font-display text-[18px]">{data!.match_info.winner}</span>}
              foot={data!.match_info.margin}
            />
            <Kpi
              label={`${data!.innings1!.batting_team} · Innings 1`}
              valueColor={TEAL}
              value={
                <>
                  <CountUp to={data!.innings1!.score} />
                  <span className="text-[16px] text-faint">/{data!.innings1!.wickets}</span>
                </>
              }
              foot={`${data!.innings1!.overs_completed} ov · RR ${runRate(data!.innings1)}`}
            />
            <Kpi
              label={`${data!.innings2!.batting_team} · Innings 2`}
              value={
                <>
                  <CountUp to={data!.innings2!.score} />
                  <span className="text-[16px] text-faint">/{data!.innings2!.wickets}</span>
                </>
              }
              foot={`${data!.innings2!.overs_completed} ov · RR ${runRate(data!.innings2)}`}
            />
            <Kpi
              label="Top Scoring Over"
              value={
                <CountUp
                  to={best!.runs}
                  suffix={<span className="ml-[3px] text-[13px] text-faint">runs</span>}
                />
              }
              foot={best!.team ? `${best!.team} · over ${best!.over}` : "—"}
            />
          </>
        ) : (
          [0, 1, 2, 3].map((i) => (
            <div key={i} className="rounded-md border border-edge bg-surface px-4 py-[14px]">
              <div className="skel mb-2 h-3 w-20" />
              <div className="skel h-7 w-16" />
            </div>
          ))
        )}
      </div>

      {/* Re-simulate control */}
      <div className="mb-4 flex justify-end">
        <button
          onClick={run}
          disabled={loading}
          className="flex items-center gap-2 rounded-md border border-edge bg-elevated px-4 py-2 text-[12px] font-medium text-muted transition-colors hover:border-accent/50 hover:text-ink disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          {loading ? "Simulating…" : "Re-simulate match"}
        </button>
      </div>

      <ChartPanel
        title="Manhattan · Runs per Over"
        meta="1–20 OVERS · RUNS"
        team1={team1}
        team2={team2}
        loading={!ready}
      >
        <BarChart data={manhattan} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="2 4" vertical={false} stroke={EDGE} />
          <XAxis dataKey="over" tick={axisTick} axisLine={false} tickLine={false} dy={6} interval={1} />
          <YAxis tick={axisTick} axisLine={false} tickLine={false} width={40} />
          <Tooltip cursor={{ fill: "rgba(255,255,255,0.03)" }} content={<TerminalTooltip />} />
          <Bar dataKey={team1} fill={TEAL} radius={[2, 2, 0, 0]} maxBarSize={16} />
          <Bar dataKey={team2} fill={COOL} radius={[2, 2, 0, 0]} maxBarSize={16} />
        </BarChart>
      </ChartPanel>

      <ChartPanel
        title="Worm · Cumulative Runs"
        meta="0–20 OVERS · CUMULATIVE"
        team1={team1}
        team2={team2}
        loading={!ready}
      >
        <LineChart data={worm} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="2 4" vertical={false} stroke={EDGE} />
          <XAxis dataKey="over" tick={axisTick} axisLine={false} tickLine={false} dy={6} interval={1} />
          <YAxis tick={axisTick} axisLine={false} tickLine={false} width={40} />
          <Tooltip content={<TerminalTooltip />} />
          <Line
            type="monotone"
            dataKey={team1}
            stroke={TEAL}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, strokeWidth: 0 }}
          />
          <Line
            type="monotone"
            dataKey={team2}
            stroke={COOL}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, strokeWidth: 0 }}
          />
        </LineChart>
      </ChartPanel>
    </div>
  );
}

const axisTick = {
  fill: FAINT,
  fontSize: 11,
  fontFamily: "var(--font-mono)",
} as const;

function ChartPanel({
  title,
  meta,
  team1,
  team2,
  loading,
  children,
}: {
  title: string;
  meta: string;
  team1: string;
  team2: string;
  loading: boolean;
  children: React.ReactElement;
}) {
  return (
    <Panel
      title={title}
      className="mb-4"
      right={
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-2 font-mono text-[11px] text-muted">
            <span className="inline-block h-[7px] w-[7px] rounded-full" style={{ background: TEAL }} />
            {team1 || "—"}
          </span>
          <span className="flex items-center gap-2 font-mono text-[11px] text-muted">
            <span className="inline-block h-[7px] w-[7px] rounded-full" style={{ background: COOL }} />
            {team2 || "—"}
          </span>
          <span className="hidden font-mono text-[11px] text-faint sm:inline">{meta}</span>
        </div>
      }
    >
      <div className="h-[300px] w-full">
        {loading ? (
          <div className="skel h-full w-full" />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            {children}
          </ResponsiveContainer>
        )}
      </div>
    </Panel>
  );
}

/* eslint-disable @typescript-eslint/no-explicit-any */
function TerminalTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded-[6px] border border-edge px-3 py-2 font-mono text-[11px]"
      style={{ background: SURFACE }}
    >
      <div className="mb-1 uppercase tracking-[0.08em] text-faint">{label}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-2 text-muted">
            <span
              className="inline-block h-[7px] w-[7px] rounded-full"
              style={{ background: p.color }}
            />
            {p.dataKey}
          </span>
          <span className="tnum text-ink">{p.value}</span>
        </div>
      ))}
    </div>
  );
}
