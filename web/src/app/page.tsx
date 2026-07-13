import {
  fetchChampionshipOdds,
  fetchTeamStats,
  type ChampionshipOdd,
  type TeamStat,
} from "@/lib/api";
import { heatColor } from "@/lib/design";
import { CountUp, HeatBar, Reveal } from "@/components/motion";
import {
  EmptyState,
  HeatRamp,
  Kpi,
  PageHead,
  Panel,
  fullName,
  tdBase,
  thBase,
  thL,
} from "@/components/ui";

/**
 * Real Monte Carlo sample size behind the aggregate odds. This matches
 * `scripts/run_tournament.py` (`simulate_multiple_seasons(teams, n=500)`) and the
 * committed `output/tournament_results.csv`. Kept truthful — do NOT inflate it.
 */
const SIMULATED_SEASONS = 500;

export default async function Home() {
  const [odds, teams] = await Promise.all([
    fetchChampionshipOdds(),
    fetchTeamStats(),
  ]);

  // Backend offline / no data yet — render an honest empty state, not a crash.
  if (odds.length === 0 && teams.length === 0) {
    return (
      <EmptyState title="Season Overview">
        No simulation data available. Start the API server
        <span className="font-mono text-faint"> (uvicorn src.api.server:app)</span> and reload.
      </EmptyState>
    );
  }

  const ranked = [...teams].sort((a, b) => b.overall_strength - a.overall_strength);

  // Heat domains, derived from the real field so the ramp always spans it.
  const maxChamp = Math.max(0, ...odds.map((o) => o.championship_probability));
  const overalls = teams.map((t) => t.overall_strength);
  const oMin = overalls.length ? Math.min(...overalls) : 0;
  const oMax = overalls.length ? Math.max(...overalls) : 100;

  const champion = odds[0];
  const topStrength = ranked[0];
  const fieldSize = odds.length || teams.length;

  return (
    <div>
      <PageHead
        title="Season Overview"
        sub={
          <>
            Monte&nbsp;Carlo projection across{" "}
            <b className="font-semibold text-ink">{fieldSize} franchises</b> · ratings derived
            from real Cricsheet ball-by-ball data
          </>
        }
        metaLabel="Model"
        metaValue="ball-by-ball · v0.2"
      />

      {/* KPI strip */}
      <Reveal as="div" className="mb-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Kpi
          label="Projected Champion"
          value={
            <CountUp
              to={champion?.championship_probability ?? 0}
              decimals={1}
              suffix={<span className="ml-[2px] text-[13px] text-faint">%</span>}
            />
          }
          foot={
            champion ? (
              <>
                <span className="font-display font-semibold text-ink">{champion.team_id}</span>{" "}
                {fullName(champion.name, champion.team_id)}
              </>
            ) : (
              "—"
            )
          }
        />
        <Kpi
          label="Top Strength Index"
          valueColor={
            topStrength ? heatColor(topStrength.overall_strength, oMin, oMax) : undefined
          }
          value={<CountUp to={topStrength?.overall_strength ?? 0} decimals={1} />}
          foot={
            topStrength ? (
              <>
                <span className="font-display font-semibold text-ink">{topStrength.team_id}</span>{" "}
                Overall · Playing XI
              </>
            ) : (
              "—"
            )
          }
        />
        <Kpi
          label="Field Size"
          value={<CountUp to={fieldSize} />}
          foot="franchises simulated"
        />
        <Kpi
          label="Sample"
          value={<CountUp to={SIMULATED_SEASONS} />}
          foot="Monte Carlo seasons"
        />
      </Reveal>

      {/* Championship probability — hero panel */}
      <Reveal as="div" delay={0.12} className="mb-4">
        <Panel
          title="Championship Probability"
          meta={`${SIMULATED_SEASONS.toLocaleString()} SIMULATED SEASONS`}
        >
          {odds.map((t: ChampionshipOdd, i: number) => {
            const color = heatColor(t.championship_probability, 0, maxChamp);
            const barPct = maxChamp > 0 ? (t.championship_probability / maxChamp) * 100 : 0;
            const isLeader = i === 0;
            return (
              <div
                key={t.team_id ?? t.name}
                className="grid grid-cols-[30px_minmax(120px,190px)_1fr_auto] items-center gap-4 border-b border-edge-soft px-[6px] py-[15px] last:border-b-0 sm:gap-[18px]"
              >
                <div className="text-right font-mono text-[13px] text-faint">
                  {String(i + 1).padStart(2, "0")}
                </div>
                <div className="flex min-w-0 items-center gap-[10px]">
                  <span
                    className="inline-block h-[26px] w-[2px] rounded-[1px]"
                    style={{ background: isLeader ? "var(--color-accent)" : "transparent" }}
                    aria-hidden
                  />
                  <div className="min-w-0">
                    <div className="font-display text-[17px] font-semibold leading-tight tracking-[-0.01em]">
                      {t.team_id}
                    </div>
                    <div className="truncate text-[12px] text-muted">
                      {fullName(t.name, t.team_id)}
                    </div>
                  </div>
                </div>
                <HeatBar pct={barPct} color={color} delay={0.2 + i * 0.05} />
                <div className="text-right">
                  <div className="font-mono tnum text-[28px] font-medium leading-none tracking-[-0.015em]">
                    <CountUp
                      to={t.championship_probability}
                      decimals={1}
                      delay={0.2 + i * 0.05}
                      suffix={<span className="ml-[1px] text-[14px] text-faint">%</span>}
                    />
                  </div>
                  <div className="mt-[3px] font-mono text-[11px] text-faint">
                    reach final {t.final_probability.toFixed(1)}%
                  </div>
                </div>
              </div>
            );
          })}
        </Panel>
      </Reveal>

      {/* Team strength index */}
      <Reveal as="div" delay={0.19}>
        <Panel title="Team Strength Index" meta="PLAYING XI · 0–100">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className={thL}>Squad</th>
                <th className={thBase}>Bat</th>
                <th className={thBase}>Bowl</th>
                <th className={thBase}>Overall</th>
              </tr>
            </thead>
            <tbody>
              {ranked.map((t: TeamStat, i: number) => {
                const color = heatColor(t.overall_strength, oMin, oMax);
                const barPct =
                  oMax > oMin ? ((t.overall_strength - oMin) / (oMax - oMin)) * 100 : 100;
                return (
                  <tr
                    key={t.team_id}
                    className="border-b border-edge-soft transition-colors last:border-b-0 hover:bg-white/[0.02]"
                  >
                    <td className="px-[10px] py-[13px] text-left">
                      <span className="inline-block min-w-[44px] font-display text-[15px] font-semibold text-ink">
                        {t.team_id}
                      </span>
                      <span className="ml-[2px] text-[11.5px] text-faint">
                        {fullName(t.name, t.team_id)}
                      </span>
                    </td>
                    <td className={tdBase}>
                      <CountUp to={t.batting_strength} decimals={1} delay={0.28 + i * 0.04} />
                    </td>
                    <td className={tdBase}>
                      <CountUp to={t.bowling_strength} decimals={1} delay={0.28 + i * 0.04} />
                    </td>
                    <td className={tdBase}>
                      <div className="flex items-center justify-end gap-[10px]">
                        <span className="text-[17px] font-semibold" style={{ color }}>
                          <CountUp
                            to={t.overall_strength}
                            decimals={1}
                            delay={0.28 + i * 0.04}
                          />
                        </span>
                        <HeatBar
                          pct={barPct}
                          color={color}
                          height={5}
                          delay={0.32 + i * 0.04}
                          className="w-16 shrink-0"
                        />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <div className="mt-[14px] mb-[2px] flex items-center gap-2 px-[10px] font-mono text-[11px] text-faint">
            <span>0</span>
            <HeatRamp />
            <span>100</span>
            <span className="ml-2">
              Overall heat-encoded · weighted bat + bowl of the projected XI
            </span>
          </div>
        </Panel>
      </Reveal>
    </div>
  );
}
