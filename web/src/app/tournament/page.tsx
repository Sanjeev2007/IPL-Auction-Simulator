import { fetchPointsTable, type PointsRow } from "@/lib/api";
import { playoffPct } from "@/lib/transforms";
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

/** Standard IPL structure: the top 4 of the league advance to the playoffs. */
const PLAYOFF_BERTHS = 4;

export default async function TournamentPage() {
  const table = await fetchPointsTable();

  if (table.length === 0) {
    return (
      <EmptyState title="Projected Standings">
        No tournament results yet. Run the season simulation
        <span className="font-mono text-faint"> (scripts/run_tournament.py)</span> and reload.
      </EmptyState>
    );
  }

  const berths = Math.min(PLAYOFF_BERTHS, table.length);
  const champion = table[0];
  const pointsLeader = table.reduce((a, b) => (b.points > a.points ? b : a), table[0]);
  const bubble = table[berths - 1]; // last team above the line

  const ptsValues = table.map((t) => t.points);
  const pMin = Math.min(...ptsValues);
  const pMax = Math.max(...ptsValues);

  return (
    <div>
      <PageHead
        title="Projected Standings"
        sub={
          <>
            League table averaged over simulated seasons ·{" "}
            <b className="font-semibold text-ink">
              top {berths} of {table.length}
            </b>{" "}
            advance to the playoffs
          </>
        }
        metaLabel="Stage"
        metaValue="league · round-robin"
      />

      <Reveal as="div" className="mb-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Kpi
          label="Projected Champion"
          value={<span className="font-display tracking-tight">{champion.team_id}</span>}
          foot={fullName(champion.name, champion.team_id) || "top of the table"}
        />
        <Kpi
          label="Points Leader"
          value={
            <CountUp
              to={pointsLeader.points}
              decimals={1}
              suffix={<span className="ml-[3px] text-[13px] text-faint">pts</span>}
            />
          }
          foot={
            <>
              <span className="font-display font-semibold text-ink">{pointsLeader.team_id}</span> ·
              season mean
            </>
          }
        />
        <Kpi
          label="Playoff Berths"
          value={
            <>
              <CountUp to={berths} />
              <span className="ml-[3px] text-[13px] text-faint">/ {table.length}</span>
            </>
          }
          foot={`cutoff after ${berths}th place`}
        />
        <Kpi
          label="On the Bubble"
          valueColor={heatColor(playoffPct(bubble, berths - 1), 0, 100)}
          value={
            <CountUp
              to={playoffPct(bubble, berths - 1)}
              suffix={<span className="ml-[2px] text-[13px] text-faint">%</span>}
            />
          }
          foot={
            <>
              <span className="font-display font-semibold text-ink">{bubble.team_id}</span> · last
              team above the line
            </>
          }
        />
      </Reveal>

      <Reveal as="div" delay={0.12}>
        <Panel title="League Table" meta="RANK · SQUAD · PTS · PLAYOFF %">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className={thBase + " w-[46px] text-left"}>Rank</th>
                <th className={thL}>Squad</th>
                <th className={thBase}>Proj Pts</th>
                <th className={thBase + " w-[220px]"}>Playoff %</th>
              </tr>
            </thead>
            <tbody>
              {table.map((t: PointsRow, idx: number) => {
                const inZone = idx < berths;
                const pct = playoffPct(t, idx);
                const pctColor = heatColor(pct, 0, 100);
                const ptsColor = heatColor(t.points, pMin, pMax);
                return (
                  <tr
                    key={t.team_id}
                    className="border-b border-edge-soft transition-colors last:border-b-0 hover:bg-white/[0.02]"
                  >
                    <td className="py-[13px] pl-[10px] text-left">
                      <div className="flex items-center gap-[10px]">
                        <span
                          className="inline-block h-[24px] w-[2px] rounded-[1px]"
                          style={{ background: inZone ? "var(--color-accent)" : "transparent" }}
                          aria-hidden
                        />
                        <span className="font-mono tnum text-[14px] text-faint">
                          {String(t.rank).padStart(2, "0")}
                        </span>
                      </div>
                    </td>
                    <td className="px-[10px] py-[13px] text-left">
                      <span className="font-display text-[15px] font-semibold text-ink">
                        {t.team_id}
                      </span>
                      <span className="ml-[6px] text-[11.5px] text-faint">
                        {fullName(t.name, t.team_id)}
                      </span>
                    </td>
                    <td className={tdBase}>
                      <span className="text-[16px] font-semibold" style={{ color: ptsColor }}>
                        <CountUp to={t.points} decimals={1} delay={0.2 + idx * 0.04} />
                      </span>
                    </td>
                    <td className="px-[10px] py-[13px]">
                      <div className="flex items-center justify-end gap-[10px]">
                        <HeatBar
                          pct={pct}
                          color={pctColor}
                          height={6}
                          delay={0.24 + idx * 0.04}
                          className="w-[120px] shrink-0"
                        />
                        <span
                          className="w-[48px] text-right font-mono tnum text-[15px] font-medium"
                          style={{ color: pctColor }}
                        >
                          <CountUp to={pct} delay={0.24 + idx * 0.04} />
                          <span className="text-[11px] text-faint">%</span>
                        </span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          <div className="mt-[14px] flex flex-wrap items-center gap-x-5 gap-y-2 px-[10px] font-mono text-[11px] text-faint">
            <span className="flex items-center gap-2">
              <span className="inline-block h-[12px] w-[2px] rounded-full bg-accent" aria-hidden />
              playoff zone (top {berths})
            </span>
            <span className="flex items-center gap-2">
              <span>0</span>
              <HeatRamp className="w-16" />
              <span>100</span>
              playoff&nbsp;% heat-encoded
            </span>
          </div>
        </Panel>
      </Reveal>
    </div>
  );
}
