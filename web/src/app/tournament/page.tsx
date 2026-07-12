import { Trophy, Medal, Star, TrendingUp } from "lucide-react";
import { fetchPointsTable, type PointsRow } from "@/lib/api";
import { playoffPct } from "@/lib/transforms";

export default async function TournamentPage() {
    const table = await fetchPointsTable();

    return (
        <div className="space-y-6 max-w-5xl mx-auto pb-10">
            <div className="bg-[#111827] text-white rounded-xl shadow-lg border border-[var(--color-espn-border)] p-8 flex items-center gap-6 relative overflow-hidden isolate">
                <div className="absolute -right-10 -top-10 text-[var(--color-espn-bg)] opacity-30 transform rotate-12">
                    <Trophy className="w-64 h-64" />
                </div>
                <div className="bg-[#1E88E5] p-3 rounded-2xl shadow-[0_0_30px_rgba(30,136,229,0.4)] relative z-10">
                    <Trophy className="w-10 h-10 text-white" />
                </div>
                <div className="relative z-10">
                    <h1 className="text-3xl sm:text-4xl font-black tracking-tight mb-2">Tournament Standings</h1>
                    <p className="text-[var(--color-espn-text-secondary)] text-sm sm:text-base font-medium max-w-xl leading-relaxed">
                        Monte Carlo aggregate analysis of 2,000 full IPL seasons. Ranks teams by mean points earned to project structural squad dominance.
                    </p>
                </div>
            </div>

            <div className="espn-card">
                <div className="espn-card-header bg-[#111827]">
                    <div className="flex items-center gap-2">
                        <Medal className="w-5 h-5 text-[var(--color-espn-secondary)]" />
                        Projected League Table (2000 Iterations)
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left whitespace-nowrap">
                        <thead className="bg-[#0B1724] border-b border-[var(--color-espn-border)] text-gray-400 uppercase tracking-widest text-[11px] font-black">
                            <tr>
                                <th className="px-6 py-4 w-16 text-center">Pos</th>
                                <th className="px-6 py-4">Franchise</th>
                                <th className="px-6 py-4 text-right">Proj. Pts</th>
                                <th className="px-6 py-4 text-center">Playoff Prob</th>
                                <th className="px-6 py-4 text-center">Outcome</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[var(--color-espn-border)] bg-[#1F2937]">
                            {table.map((t: PointsRow, idx: number) => {
                                const isQualifier = idx < 4;
                                const playoffProb = playoffPct(t, idx);
                                return (
                                    <tr
                                        key={t.team_id}
                                        className={`transition-colors group ${isQualifier ? 'hover:bg-green-900/10' : 'hover:bg-red-900/10'}`}
                                    >
                                        <td className="px-6 py-5 text-center">
                                            <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-black shadow-inner ${idx === 0 ? 'bg-[var(--color-espn-secondary)] text-[#0B1724] ring-2 ring-[var(--color-espn-secondary)]/50 ring-offset-2 ring-offset-[#1F2937]' :
                                                    idx === 1 ? 'bg-gray-300 text-gray-800' :
                                                        idx === 2 ? 'bg-[#CD7F32] text-white' :
                                                            'bg-[#111827] text-gray-400 border border-[var(--color-espn-border)]'
                                                }`}>
                                                {t.rank}
                                            </span>
                                        </td>
                                        <td className="px-6 py-5">
                                            <div className="flex items-center gap-3">
                                                <span className="font-extrabold text-xl text-white tracking-tight">{t.name}</span>
                                                {idx === 0 && <Star className="w-5 h-5 text-yellow-400 fill-yellow-400 drop-shadow-[0_0_8px_rgba(250,204,21,0.6)]" />}
                                            </div>
                                        </td>
                                        <td className="px-6 py-5 text-right">
                                            <span className="font-mono text-2xl font-black text-[var(--color-espn-primary)]">
                                                {Number(t.points).toFixed(1)}
                                            </span>
                                        </td>
                                        <td className="px-6 py-5 text-center">
                                            <div className="flex flex-col items-center">
                                                <span className="font-mono text-lg font-bold text-gray-200">
                                                    {playoffProb}%
                                                </span>
                                                <div className="w-24 h-1.5 bg-[#0B1724] rounded-full mt-2 overflow-hidden shadow-inner flex items-center">
                                                    <div
                                                        className={`h-full rounded-full ${playoffProb > 50 ? 'bg-green-500' : 'bg-red-500'}`}
                                                        style={{ width: `${playoffProb}%` }}
                                                    ></div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-5 text-center">
                                            {isQualifier ? (
                                                <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-green-500/10 text-green-400 border border-green-500/20 text-[10px] font-black rounded uppercase tracking-widest">
                                                    <TrendingUp className="w-3 h-3" />
                                                    QUALIFIER
                                                </span>
                                            ) : (
                                                <span className="inline-block px-3 py-1 bg-red-500/10 text-red-400 border border-red-500/20 text-[10px] font-black rounded uppercase tracking-widest opacity-80">
                                                    ELIMINATED
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                    <div className="bg-[#111827] px-6 py-3 border-t border-[var(--color-espn-border)] flex items-center justify-end text-xs text-[var(--color-espn-text-secondary)] italic">
                        Top 4 advance to Playoffs (Q1, E, Q2, F)
                    </div>
                </div>
            </div>
        </div>
    );
}
