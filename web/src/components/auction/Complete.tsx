"use client";

/**
 * Auction complete → squad summaries → "Simulate Tournament".
 * The button hits POST /api/auction/rooms/{code}/simulate, which assembles the
 * drafted rosters and runs a real season on the engine; we render the standings.
 */

import { useState } from "react";
import { clsx } from "clsx";
import { Crown, Play, Trophy } from "lucide-react";
import { Panel, PageHead, Kpi, thBase, thL, tdBase } from "@/components/ui";
import { CountUp, HeatBar, Reveal } from "@/components/motion";
import { heatColor } from "@/lib/design";
import { SquadPanel } from "@/components/auction/SquadPanel";
import type { LiveState } from "@/hooks/useAuctionSocket";
import { simulateRoom, type Creds, type SimulateRoomResp } from "@/lib/auction";

export function Complete({ state, me }: { state: LiveState; me: Creds }) {
  const participants = state.complete?.state.participants ?? state.participants;
  const cfg = state.config;
  const min = cfg?.squad_min ?? 11;
  const validCount = participants.filter((p) => p.squad_size >= min).length;

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SimulateRoomResp | null>(null);

  async function runSim() {
    setBusy(true);
    setError(null);
    try {
      setResult(await simulateRoom(state.code));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed.");
    } finally {
      setBusy(false);
    }
  }

  const ptsValues = result?.standings.map((s) => s.points) ?? [];
  const pMin = ptsValues.length ? Math.min(...ptsValues) : 0;
  const pMax = ptsValues.length ? Math.max(...ptsValues) : 1;

  // Playoff results carry team_ids; map them to the drafted display names.
  const nameOf = (id: string) =>
    result?.standings.find((s) => s.team_id === id)?.team_name ?? id;

  return (
    <div>
      <PageHead
        title="Auction Complete"
        sub="Every lot is resolved. Review the drafted squads, then run a full season on the engine."
        metaLabel="Room"
        metaValue={state.code}
      />

      {/* Squad summaries */}
      <Reveal as="div" className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {participants.map((p) => (
          <SquadPanel key={p.id} p={p} config={cfg} isMe={p.id === me.participant_id} />
        ))}
      </Reveal>

      {/* Simulate control */}
      {!result && (
        <Reveal as="div" delay={0.05}>
          <Panel title="Run the Tournament" meta="ENGINE · REAL SEASON">
            <div className="flex flex-wrap items-center justify-between gap-4 pt-1">
              <p className="max-w-xl text-[13px] leading-relaxed text-muted">
                Each squad is reduced to a best XI and played through a full league + playoffs on the
                ball-by-ball engine.{" "}
                {validCount < 2 && (
                  <span className="text-[color:var(--color-warm)]">
                    Need at least 2 squads with {min}+ players — only {validCount} qualify.
                  </span>
                )}
              </p>
              <button onClick={runSim} disabled={busy || validCount < 2} className="cta-accent px-5 py-2.5 text-[14px]">
                <Play className="h-4 w-4" />
                {busy ? "Simulating…" : "Simulate Tournament"}
              </button>
            </div>
            {error && (
              <div className="mt-3 rounded-md border border-hot/40 bg-hot/5 px-3 py-2 font-mono text-[12px] text-[color:var(--color-hot)]">
                {error}
              </div>
            )}
          </Panel>
        </Reveal>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          <Reveal as="div" className="grid grid-cols-2 gap-4 lg:grid-cols-3">
            <Kpi
              label="Champion"
              value={
                <span className="flex items-center gap-2 font-display tracking-tight">
                  <Trophy className="h-5 w-5 text-accent" />
                  {result.champion?.team_name ?? "—"}
                </span>
              }
              foot="won the final"
            />
            <Kpi
              label="Runner-up"
              value={<span className="font-display tracking-tight">{result.runner_up?.team_name ?? "—"}</span>}
              foot="lost the final"
            />
            <Kpi
              label="Teams"
              value={<CountUp to={result.team_count} />}
              foot={result.skipped.length ? `${result.skipped.length} skipped (short squad)` : "all squads qualified"}
            />
          </Reveal>

          <Reveal as="div" delay={0.08}>
            <Panel title="Final Standings" meta="RANK · TEAM · W-L · PTS · NRR">
              <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className={thBase + " w-[46px] text-left"}>Rank</th>
                    <th className={thL}>Team</th>
                    <th className={thBase}>W</th>
                    <th className={thBase}>L</th>
                    <th className={thBase}>Pts</th>
                    <th className={thBase + " w-[200px]"}>NRR</th>
                  </tr>
                </thead>
                <tbody>
                  {result.standings.map((s, idx) => {
                    const champ = result.champion?.team_id === s.team_id;
                    const ptsColor = heatColor(s.points, pMin, pMax);
                    return (
                      <tr key={s.team_id} className="border-b border-edge-soft last:border-b-0 hover:bg-white/[0.02]">
                        <td className="py-[13px] pl-[10px] text-left">
                          <span className="flex items-center gap-[10px]">
                            <span
                              className="inline-block h-[24px] w-[2px] rounded-[1px]"
                              style={{ background: champ ? "var(--color-accent)" : "transparent" }}
                              aria-hidden
                            />
                            <span className="font-mono tnum text-[14px] text-faint">
                              {String(s.rank).padStart(2, "0")}
                            </span>
                          </span>
                        </td>
                        <td className="px-[10px] py-[13px] text-left">
                          <span className="flex items-center gap-2">
                            <span className={clsx("text-[14px] font-semibold", champ ? "text-ink" : "text-ink")}>
                              {s.team_name}
                            </span>
                            {champ && <Crown className="h-[13px] w-[13px] text-warm" aria-label="champion" />}
                          </span>
                        </td>
                        <td className={tdBase}>{s.wins}</td>
                        <td className={tdBase}>{s.losses}</td>
                        <td className={tdBase}>
                          <span className="text-[15px] font-semibold" style={{ color: ptsColor }}>
                            <CountUp to={s.points} delay={0.15 + idx * 0.04} />
                          </span>
                        </td>
                        <td className="px-[10px] py-[13px]">
                          <span className="flex items-center justify-end gap-[10px]">
                            <HeatBar
                              pct={((s.nrr + 2) / 4) * 100}
                              color={heatColor(s.nrr, -1.5, 1.5)}
                              height={6}
                              delay={0.2 + idx * 0.04}
                              className="hidden w-[110px] shrink-0 sm:block"
                            />
                            <span
                              className="w-[54px] text-right font-mono tnum text-[13.5px]"
                              style={{ color: heatColor(s.nrr, -1.5, 1.5) }}
                            >
                              {s.nrr > 0 ? "+" : ""}
                              {s.nrr.toFixed(2)}
                            </span>
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              </div>
            </Panel>
          </Reveal>

          {Object.keys(result.playoffs).length > 0 && (
            <Reveal as="div" delay={0.12}>
              <Panel title="Playoffs" meta="BRACKET">
                <ul className="grid gap-2 pt-1 sm:grid-cols-2">
                  {Object.entries(result.playoffs).map(([label, m]) => {
                    const tie = m.winner === "Tie";
                    const loser = m.winner === m.team1 ? m.team2 : m.team1;
                    return (
                      <li key={label} className="rounded-md border border-edge-soft bg-bg/40 px-3 py-2.5">
                        <div className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">{label}</div>
                        <div className="mt-1 text-[13px] leading-snug">
                          {tie ? (
                            <span className="text-muted">
                              {nameOf(m.team1)} vs {nameOf(m.team2)} — tie
                            </span>
                          ) : (
                            <>
                              <span className="font-semibold text-ink">{nameOf(m.winner)}</span>
                              <span className="text-muted">
                                {" "}beat {nameOf(loser)}
                                {m.margin ? ` · ${m.margin}` : ""}
                              </span>
                            </>
                          )}
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </Panel>
            </Reveal>
          )}
        </div>
      )}
    </div>
  );
}
