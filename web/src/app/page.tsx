import Link from "next/link";
import { Trophy, Shield, Play, BarChart2 } from "lucide-react";
import {
  fetchChampionshipOdds,
  fetchTeamStats,
  type ChampionshipOdd,
  type TeamStat,
} from "@/lib/api";
import { normalizeBarWidth } from "@/lib/transforms";

export default async function Home() {
  const [odds, teams] = await Promise.all([
    fetchChampionshipOdds(),
    fetchTeamStats(),
  ]);

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-6 pb-4 border-b border-[var(--color-espn-border)]">
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-2">
            Simulation Overview
          </h1>
          <p className="text-[var(--color-espn-text-secondary)] text-sm sm:text-base max-w-2xl">
            Derived from 2,000 deep Monte Carlo simulations powered by precision probability
            models integrating IPL & international historical data.
          </p>
        </div>
        <Link
          href="/simulator"
          className="bg-[var(--color-espn-primary)] hover:bg-[#1565C0] text-white px-6 py-3 rounded-lg font-bold shadow-lg shadow-[var(--color-espn-primary)]/20 transition-all flex items-center space-x-2 whitespace-nowrap group"
        >
          <Play fill="currentColor" className="w-4 h-4 text-white group-hover:scale-110 transition-transform" />
          <span>Launch Simulator</span>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Championship Odds */}
        <div className="espn-card">
          <div className="espn-card-header">
            <div className="flex items-center space-x-2">
              <Trophy className="w-5 h-5 text-[var(--color-espn-secondary)]" />
              <span>To Win Championship</span>
            </div>
            <span className="text-xs font-normal text-[var(--color-espn-text-secondary)]">
              SIMULATED PROBABILITY
            </span>
          </div>
          <div className="p-5 space-y-5">
            {odds.map((t: ChampionshipOdd, idx: number) => {
              const prob = t.championship_probability;
              // Normalize for bar width against the highest prob.
              const barWidth = normalizeBarWidth(
                prob,
                odds[0]?.championship_probability ?? 0
              );
              const isTop = idx === 0;

              return (
                <div key={t.team_id ?? t.name} className="relative group">
                  <div className="flex justify-between items-center mb-1.5">
                    <div className="flex items-center space-x-3">
                      <span className={`text-xs font-black w-4 text-right ${isTop ? 'text-[var(--color-espn-secondary)]' : 'text-gray-500'}`}>
                        {idx + 1}
                      </span>
                      <span className="font-bold text-white tracking-wide">
                        {t.name}
                      </span>
                    </div>
                    <div className="flex items-baseline space-x-3">
                      <span className="text-xs text-[var(--color-espn-text-secondary)]">
                        FINAL: {t.final_probability}%
                      </span>
                      <span className={`font-black text-lg ${isTop ? 'text-[var(--color-espn-primary)]' : 'text-gray-300'}`}>
                        {prob}%
                      </span>
                    </div>
                  </div>
                  <div className="w-full bg-[#374151] rounded-full h-2.5 overflow-hidden">
                    <div
                      className={`h-2.5 rounded-full ${isTop ? 'bg-[var(--color-espn-secondary)]' : 'bg-[var(--color-espn-primary)]'}`}
                      style={{ width: barWidth }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Team Strengths */}
        <div className="espn-card">
          <div className="espn-card-header">
            <div className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-gray-300" />
              <span>Team Strength Index</span>
            </div>
            <span className="text-xs font-normal text-[var(--color-espn-text-secondary)]">
              BASED ON PLAYING XI
            </span>
          </div>
          <div className="p-0">
            <table className="w-full text-sm text-left">
              <thead className="bg-[#1F2937] border-b border-[var(--color-espn-border)] text-[var(--color-espn-text-secondary)] uppercase text-xs font-bold tracking-wider">
                <tr>
                  <th className="px-5 py-4">Squad</th>
                  <th className="px-5 py-4 text-center">Batting</th>
                  <th className="px-5 py-4 text-center">Bowling</th>
                  <th className="px-5 py-4 text-right">Overall Rating</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-espn-border)]">
                {teams.map((t: TeamStat, idx: number) => {
                  const ovrWidth = normalizeBarWidth(t.overall_strength, 100);
                  return (
                    <tr key={t.team_id} className="hover:bg-white/5 transition-colors group">
                      <td className="px-5 py-4">
                        <div className="flex items-center space-x-3">
                          <span className="font-bold text-white tracking-wide">{t.team_id}</span>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-center">
                        <span className="px-2.5 py-1 rounded bg-[#374151] text-gray-300 font-bold text-xs">
                          {t.batting_strength}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-center">
                        <span className="px-2.5 py-1 rounded bg-[#374151] text-gray-300 font-bold text-xs">
                          {t.bowling_strength}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <div className="flex flex-col items-end">
                          <span className={`font-extrabold text-lg ${idx < 2 ? 'text-[var(--color-espn-secondary)]' : 'text-white'}`}>
                            {t.overall_strength}
                          </span>
                          <div className="w-20 bg-[#374151] rounded-full h-1 mt-1 overflow-hidden opacity-50 group-hover:opacity-100 transition-opacity">
                            <div className="h-full bg-white rounded-full" style={{ width: ovrWidth }}></div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="bg-[#111827] px-5 py-3 border-t border-[var(--color-espn-border)] flex items-center gap-2 text-xs text-[var(--color-espn-text-secondary)]">
            <BarChart2 className="w-3.5 h-3.5" />
            <span>Rating dynamically aggregated from phase-specific stat metrics</span>
          </div>
        </div>
      </div>
    </div>
  );
}
