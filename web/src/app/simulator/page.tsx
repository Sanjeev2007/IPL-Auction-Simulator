"use client";

/**
 * Match Simulator — pick two squads, run one full T20 fixture.
 *
 * Precision Terminal port of design/comps/simulator.html. Real data only:
 * `fetchTeamStats` powers the squad pickers + strength cards, `simulateMatch`
 * runs the ball-by-ball engine. Pre-sim state is a real skeleton so the page has
 * a first impression before you click.
 */

import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, AlertCircle } from "lucide-react";
import {
  fetchTeamStats,
  simulateMatch,
  type Innings,
  type MatchResult,
  type TeamStat,
} from "@/lib/api";
import { heatColor } from "@/lib/design";
import { CountUp, HeatBar } from "@/components/motion";
import { EmptyState, PageHead, Panel, fullName, tdBase, thBase, thL } from "@/components/ui";

export default function SimulatorPage() {
  const [teams, setTeams] = useState<TeamStat[]>([]);
  const [loadingTeams, setLoadingTeams] = useState(true);
  const [idA, setIdA] = useState("");
  const [idB, setIdB] = useState("");
  const [match, setMatch] = useState<MatchResult | null>(null);
  const [simulating, setSimulating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchTeamStats()
      .then((t) => {
        setTeams(t);
        if (t.length >= 2) {
          setIdA(t[0].team_id);
          setIdB(t[1].team_id);
        }
      })
      .finally(() => setLoadingTeams(false));
  }, []);

  const [oMin, oMax] = useMemo(() => {
    const o = teams.map((t) => t.overall_strength);
    return o.length ? [Math.min(...o), Math.max(...o)] : [0, 100];
  }, [teams]);

  const teamA = teams.find((t) => t.team_id === idA);
  const teamB = teams.find((t) => t.team_id === idB);

  const handleSimulate = async () => {
    if (!idA || !idB || idA === idB) return;
    setError("");
    setSimulating(true);
    setMatch(null);
    try {
      setMatch(await simulateMatch(idA, idB));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed.");
    } finally {
      setSimulating(false);
    }
  };

  if (!loadingTeams && teams.length < 2) {
    return (
      <EmptyState title="Match Simulator">
        Need at least two squads to simulate. Start the API server
        <span className="font-mono text-faint"> (uvicorn src.api.server:app)</span> and reload.
      </EmptyState>
    );
  }

  return (
    <div>
      <PageHead
        title="Match Simulator"
        sub="Pick two squads and simulate a single T20 fixture — one full ball-by-ball innings apiece."
        metaLabel="Format"
        metaValue="best of 1 · 20 overs"
      />

      {/* Matchup */}
      <Panel title="Matchup" meta="SELECT SQUADS · STRENGTH 0–100" className="mb-4">
        <div className="grid grid-cols-1 items-stretch gap-4 md:grid-cols-[1fr_auto_1fr]">
          <TeamCard
            side="A"
            team={teamA}
            teams={teams}
            otherId={idB}
            onSelect={setIdA}
            oMin={oMin}
            oMax={oMax}
            loading={loadingTeams}
          />

          <div className="flex flex-row items-center justify-center gap-4 md:flex-col">
            <span className="font-display text-[13px] font-semibold tracking-[0.2em] text-faint">
              VS
            </span>
            <button
              onClick={handleSimulate}
              disabled={simulating || !idA || !idB || idA === idB}
              className="cta-accent px-5 py-2.5 text-[13px]"
            >
              {simulating ? (
                <span className="tnum">SIMULATING…</span>
              ) : (
                <>
                  <Play className="h-4 w-4" fill="currentColor" />
                  Simulate Match
                </>
              )}
            </button>
          </div>

          <TeamCard
            side="B"
            team={teamB}
            teams={teams}
            otherId={idA}
            onSelect={setIdB}
            oMin={oMin}
            oMax={oMax}
            loading={loadingTeams}
            align="right"
          />
        </div>
        <div className="mt-[14px] flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[11px] text-faint">
          <span>Ball-by-ball probabilistic model on real Cricsheet data</span>
          <span className="h-[3px] w-[3px] rounded-full bg-edge" aria-hidden />
          <span>each run reseeds — scorecards vary</span>
        </div>
      </Panel>

      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-md border border-hot/40 bg-hot/10 px-4 py-3 text-[13px] text-hot">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Result */}
      <AnimatePresence mode="wait">
        {simulating ? (
          <motion.div key="skel" exit={{ opacity: 0 }}>
            <ResultSkeleton />
          </motion.div>
        ) : match ? (
          <motion.div
            key={match.match_info.match_id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.34, ease: "easeOut" }}
            className="space-y-4"
          >
            <ResultBanner match={match} />
            <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
              {[match.innings1, match.innings2].filter(Boolean).map((inn, i) => (
                <InningsCard key={i} inn={inn as Innings} />
              ))}
            </div>
            <FallOfWickets match={match} />
          </motion.div>
        ) : (
          <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <ResultSkeleton idle />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Team selector card                                                  */
/* ------------------------------------------------------------------ */

function TeamCard({
  side,
  team,
  teams,
  otherId,
  onSelect,
  oMin,
  oMax,
  loading,
  align = "left",
}: {
  side: "A" | "B";
  team?: TeamStat;
  teams: TeamStat[];
  otherId: string;
  onSelect: (id: string) => void;
  oMin: number;
  oMax: number;
  loading: boolean;
  align?: "left" | "right";
}) {
  const color = team ? heatColor(team.overall_strength, oMin, oMax) : "var(--color-muted)";
  return (
    <div className="rounded-md border border-edge bg-elevated/40 p-4">
      <div
        className={`mb-3 flex items-center justify-between gap-2 ${
          align === "right" ? "flex-row-reverse" : ""
        }`}
      >
        <span className="font-mono text-[10.5px] uppercase tracking-[0.08em] text-faint">
          Squad {side}
        </span>
        <select
          value={team?.team_id ?? ""}
          onChange={(e) => onSelect(e.target.value)}
          disabled={loading}
          className="max-w-[150px] truncate rounded border border-edge bg-surface px-2 py-1 font-mono text-[12px] text-muted outline-none focus:border-accent"
        >
          {teams.map((t) => (
            <option key={t.team_id} value={t.team_id} disabled={t.team_id === otherId}>
              {t.team_id}
            </option>
          ))}
        </select>
      </div>

      <div className={align === "right" ? "text-right" : ""}>
        <div className="font-display text-[26px] font-semibold leading-none tracking-[-0.01em]">
          {team?.team_id ?? "—"}
        </div>
        <div className="mt-1 truncate text-[12px] text-muted">
          {team ? fullName(team.name, team.team_id) || " " : " "}
        </div>
      </div>

      <div className="mt-3 space-y-2">
        <StatLine label="Bat" value={team?.batting_strength} min={oMin} max={oMax} />
        <StatLine label="Bowl" value={team?.bowling_strength} min={oMin} max={oMax} />
        <div className="flex items-center justify-between gap-3 border-t border-edge-soft pt-2">
          <span className="font-mono text-[10.5px] uppercase tracking-[0.08em] text-faint">
            Overall
          </span>
          <span className="font-mono tnum text-[18px] font-semibold" style={{ color }}>
            {team ? team.overall_strength.toFixed(1) : "—"}
          </span>
        </div>
      </div>
    </div>
  );
}

function StatLine({
  label,
  value,
  min,
  max,
}: {
  label: string;
  value?: number;
  min: number;
  max: number;
}) {
  const has = typeof value === "number";
  const color = has ? heatColor(value!, min, max) : "var(--color-edge)";
  const pct = has && max > min ? ((value! - min) / (max - min)) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="w-8 font-mono text-[10.5px] uppercase tracking-[0.06em] text-faint">
        {label}
      </span>
      <HeatBar pct={pct} color={color} height={5} className="flex-1" />
      <span className="w-9 text-right font-mono tnum text-[12px] text-muted">
        {has ? value!.toFixed(1) : "—"}
      </span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Result banner                                                       */
/* ------------------------------------------------------------------ */

function runRate(inn: Innings | null): string {
  if (!inn) return "—";
  const overs = parseFloat(String(inn.overs_completed)) || 0;
  return overs > 0 ? (inn.score / overs).toFixed(2) : "0.00";
}

function ResultBanner({ match }: { match: MatchResult }) {
  const { match_info: info, innings1: i1, innings2: i2 } = match;
  const winner = info.winner;
  return (
    <Panel
      title="Result"
      meta={info.summary?.toUpperCase()}
      bodyClassName="px-4 py-5 sm:px-6"
    >
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">
        <BannerTeam inn={i1} won={winner === info.team1} align="right" />
        <div className="flex flex-col items-center gap-1 px-2">
          <span className="font-mono text-[11px] uppercase tracking-[0.12em] text-faint">def</span>
          <span className="text-center font-display text-[13px] font-semibold leading-tight text-ink">
            {info.margin}
          </span>
        </div>
        <BannerTeam inn={i2} won={winner === info.team2} align="left" />
      </div>
    </Panel>
  );
}

function BannerTeam({
  inn,
  won,
  align,
}: {
  inn: Innings | null;
  won: boolean;
  align: "left" | "right";
}) {
  if (!inn) return <div />;
  const right = align === "right";
  return (
    <div className={right ? "text-right" : "text-left"}>
      <div className={`flex items-center gap-2 ${right ? "justify-end" : ""}`}>
        {won && <span className="h-4 w-[2px] rounded-full bg-accent" aria-hidden />}
        <span
          className="font-display text-[24px] font-semibold leading-none tracking-[-0.01em]"
          style={won ? { color: "var(--color-accent)" } : undefined}
        >
          {inn.batting_team}
        </span>
      </div>
      <div className="mt-2 font-mono tnum text-[30px] font-medium leading-none">
        <CountUp to={inn.score} />
        <span className="text-[18px] text-faint">/{inn.wickets}</span>
      </div>
      <div className="mt-1.5 font-mono text-[11px] text-faint">
        {inn.overs_completed} ov · RR {runRate(inn)}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Innings scorecard (batting + bowling)                               */
/* ------------------------------------------------------------------ */

function InningsCard({ inn }: { inn: Innings }) {
  const maxRuns = Math.max(1, ...inn.batter_scorecards.map((b) => b.runs));
  return (
    <Panel
      title={`${inn.batting_team} Innings`}
      meta={`${inn.score}/${inn.wickets} · ${inn.overs_completed} OV`}
      bodyClassName="px-0 pb-0"
    >
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className={thL + " pl-[18px]"}>Batter</th>
              <th className={thBase}>R</th>
              <th className={thBase}>B</th>
              <th className={thBase}>4s</th>
              <th className={thBase}>6s</th>
              <th className={thBase + " pr-[18px]"}>SR</th>
            </tr>
          </thead>
          <tbody>
            {inn.batter_scorecards.map((b, i) => (
              <tr key={i} className="border-b border-edge-soft transition-colors hover:bg-white/[0.02]">
                <td className="py-[11px] pl-[18px] pr-2 text-left">
                  <div className="font-display text-[13.5px] font-semibold text-ink">{b.name}</div>
                  <div className="truncate text-[11px] text-faint">{b.dismissal}</div>
                </td>
                <td className={tdBase}>
                  <span
                    className="font-semibold"
                    style={{ color: heatColor(b.runs, 0, maxRuns) }}
                  >
                    {b.runs}
                  </span>
                </td>
                <td className={tdBase}>{b.balls_faced}</td>
                <td className={tdBase}>{b.fours}</td>
                <td className={tdBase}>{b.sixes}</td>
                <td className={tdBase + " pr-[18px]"}>{b.strike_rate.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="border-t border-edge bg-elevated/30 px-[18px] py-2 font-mono text-[10.5px] uppercase tracking-[0.09em] text-faint">
        Bowling
      </div>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className={thL + " pl-[18px]"}>Bowler</th>
              <th className={thBase}>O</th>
              <th className={thBase}>R</th>
              <th className={thBase}>W</th>
              <th className={thBase + " pr-[18px]"}>ECON</th>
            </tr>
          </thead>
          <tbody>
            {inn.bowler_figures.map((b, i) => (
              <tr key={i} className="border-b border-edge-soft transition-colors last:border-b-0 hover:bg-white/[0.02]">
                <td className="py-[11px] pl-[18px] pr-2 text-left font-display text-[13.5px] font-semibold text-ink">
                  {b.name}
                </td>
                <td className={tdBase}>{b.overs}</td>
                <td className={tdBase}>{b.runs_conceded}</td>
                <td className={tdBase}>
                  <span
                    className="font-semibold"
                    style={{ color: heatColor(b.wickets, 0, 3) }}
                  >
                    {b.wickets}
                  </span>
                </td>
                <td className={tdBase + " pr-[18px]"}>{b.economy.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

/* ------------------------------------------------------------------ */
/* Fall of wickets                                                     */
/* ------------------------------------------------------------------ */

function FallOfWickets({ match }: { match: MatchResult }) {
  const innings = [match.innings1, match.innings2].filter(Boolean) as Innings[];
  return (
    <Panel title="Fall of Wickets" meta="OVER · SCORE-WKT">
      <div className="grid grid-cols-1 gap-x-10 gap-y-2 md:grid-cols-2">
        {innings.map((inn, i) => (
          <div key={i}>
            <div className="mb-3 font-mono text-[10.5px] uppercase tracking-[0.09em] text-faint">
              {inn.batting_team}
            </div>
            {inn.wicket_timeline.length === 0 ? (
              <div className="py-2 text-[12px] italic text-faint">
                No wickets fell during this innings.
              </div>
            ) : (
              <ol className="ml-1 space-y-0 border-l border-edge">
                {inn.wicket_timeline.map((w, wi) => (
                  <li key={wi} className="relative py-2 pl-5">
                    <span
                      className="absolute left-[-4px] top-[14px] h-[7px] w-[7px] rounded-full border border-hot bg-bg"
                      aria-hidden
                    />
                    <div className="flex items-baseline justify-between gap-3">
                      <span className="font-display text-[13px] font-semibold text-ink">
                        {w.batter_out}
                      </span>
                      <span className="font-mono tnum text-[12px] text-muted">
                        {w.score}-{w.wicket_number}
                      </span>
                    </div>
                    <div className="font-mono text-[11px] text-faint">
                      {w.over}.{w.ball} ov
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </div>
        ))}
      </div>
    </Panel>
  );
}

/* ------------------------------------------------------------------ */
/* Skeleton / idle pre-sim state                                       */
/* ------------------------------------------------------------------ */

function ResultSkeleton({ idle = false }: { idle?: boolean }) {
  const meta = idle ? "AWAITING SIM" : "SIMULATING…";
  return (
    <div className="space-y-4">
      <Panel title="Result" meta={meta} bodyClassName="px-6 py-5">
        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">
          <div className="space-y-2">
            <div className="skel ml-auto h-6 w-16" />
            <div className="skel ml-auto h-8 w-24" />
          </div>
          <div className="skel h-4 w-10" />
          <div className="space-y-2">
            <div className="skel h-6 w-16" />
            <div className="skel h-8 w-24" />
          </div>
        </div>
      </Panel>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {[0, 1].map((i) => (
          <Panel key={i} title="Batting" meta="—" bodyClassName="space-y-2 py-4">
            {[0, 1, 2, 3].map((r) => (
              <div key={r} className="skel h-5 w-full" />
            ))}
          </Panel>
        ))}
      </div>
    </div>
  );
}
