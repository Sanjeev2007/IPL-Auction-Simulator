"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Activity, AlertCircle, ArrowRight } from "lucide-react";
import { API_BASE } from "@/lib/api";

export default function SimulatorPage() {
    const [isSimulating, setIsSimulating] = useState(false);
    const [matchData, setMatchData] = useState<any>(null);
    const [error, setError] = useState("");

    const handleSimulate = async () => {
        setError("");
        setIsSimulating(true);
        setMatchData(null);

        try {
            // Play the next scheduled mock match
            const playRes = await fetch(`${API_BASE}/mock/play_next`, { method: "POST" });
            if (!playRes.ok) {
                const err = await playRes.json().catch(() => ({}));
                throw new Error(err.detail || "Simulation failed — start the league first.");
            }
            const played = await playRes.json();
            if (played.status === "finished") throw new Error("All matches have been played. Restart the league.");

            // Fetch full scorecard for detailed display
            const scRes = await fetch(`${API_BASE}/mock/scorecard/${played.match_id}`, { cache: "no-store" });
            if (!scRes.ok) throw new Error("Could not load scorecard");
            const data = await scRes.json();
            setMatchData(data);
        } catch (err: any) {
            setError(err.message || "Something went wrong.");
        } finally {
            setIsSimulating(false);
        }
    };

    return (
        <div className="space-y-6 pb-20">
            {/* Control Panel */}
            <div className="espn-card p-6 border-l-4 border-l-[var(--color-espn-primary)]">
                <h2 className="text-xl font-bold mb-5 flex items-center gap-2 text-white tracking-tight">
                    <Activity className="w-6 h-6 text-[var(--color-espn-primary)]" />
                    Match Simulation Engine
                </h2>

                <div className="flex flex-col sm:flex-row items-center gap-5">
                    <p className="flex-1 text-[var(--color-espn-text-secondary)] text-sm">
                        Plays the next scheduled match from the mock league. Start the league first via <code className="text-[var(--color-espn-primary)]">POST /mock/start_league</code>.
                    </p>

                    <button
                        onClick={handleSimulate}
                        disabled={isSimulating}
                        className={`w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-4 rounded-lg font-black text-white text-lg tracking-wide shadow-lg transition-all ${isSimulating
                                ? "bg-gray-600 cursor-not-allowed"
                                : "bg-[var(--color-espn-primary)] hover:bg-[#1565C0] hover:shadow-[var(--color-espn-primary)]/20 shadow-md"
                            }`}
                    >
                        {isSimulating ? (
                            <span className="animate-pulse flex items-center gap-2">Simulating...</span>
                        ) : (
                            <>
                                <Play className="w-5 h-5" fill="currentColor" />
                                SIMULATE
                            </>
                        )}
                    </button>
                </div>

                {error && (
                    <div className="mt-5 p-3 bg-red-900/40 border border-red-500/50 text-red-200 rounded flex items-center gap-2 text-sm font-medium">
                        <AlertCircle className="w-5 h-5" />
                        {error}
                    </div>
                )}
            </div>

            {/* Results Area */}
            <AnimatePresence mode="wait">
                {matchData && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.98, y: 10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.98, y: -10 }}
                        transition={{ duration: 0.4, ease: "easeOut" }}
                        className="space-y-6"
                    >
                        {/* Score Banner */}
                        <div className="bg-[#111827] text-white rounded-xl shadow-2xl border border-[var(--color-espn-border)] overflow-hidden relative isolate">
                            <div className="absolute inset-0 bg-gradient-to-r from-[var(--color-espn-primary)]/10 via-transparent to-[var(--color-espn-primary)]/10 pointer-events-none"></div>

                            <div className="bg-[#0B1724] px-6 py-2.5 text-xs font-bold uppercase tracking-[0.2em] text-[var(--color-espn-secondary)] border-b border-white/5 flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                                Official Simulator Result
                            </div>

                            <div className="p-8 pb-10 text-center relative">
                                <div className="flex flex-col md:flex-row justify-center items-center gap-6 md:gap-16">
                                    {/* Team 1 */}
                                    <div className="flex-1 text-center md:text-right w-full">
                                        <div className="text-4xl md:text-6xl font-black text-white tracking-tighter glow-text">
                                            {matchData.match_info?.team1 ?? matchData.team1}
                                        </div>
                                        <div className="text-3xl md:text-4xl mt-2 font-bold text-[var(--color-espn-primary)] font-mono">
                                            {matchData.innings1?.score}/{matchData.innings1?.wickets}
                                        </div>
                                        <div className="text-sm text-[var(--color-espn-text-secondary)] mt-1 tracking-widest font-medium">
                                            {matchData.innings1?.overs_completed} OVERS
                                        </div>
                                    </div>

                                    {/* VS Badge */}
                                    <div className="hidden md:flex flex-col items-center justify-center shrink-0">
                                        <div className="w-12 h-12 bg-[#1F2937] rounded-full flex items-center justify-center font-black text-[var(--color-espn-text-secondary)] shadow-inner border border-white/5 z-10">
                                            VS
                                        </div>
                                        <div className="w-px h-16 bg-gradient-to-b from-transparent via-[var(--color-espn-border)] to-transparent absolute"></div>
                                    </div>

                                    {/* Team 2 */}
                                    <div className="flex-1 text-center md:text-left w-full">
                                        <div className="text-4xl md:text-6xl font-black text-white tracking-tighter">
                                            {matchData.match_info?.team2 ?? matchData.team2}
                                        </div>
                                        <div className="text-3xl md:text-4xl mt-2 font-bold text-[var(--color-espn-secondary)] font-mono">
                                            {matchData.innings2?.score}/{matchData.innings2?.wickets}
                                        </div>
                                        <div className="text-sm text-[var(--color-espn-text-secondary)] mt-1 tracking-widest font-medium">
                                            {matchData.innings2?.overs_completed} OVERS
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="bg-[var(--color-espn-primary)] py-3 px-6 text-center shadow-[inset_0_2px_10px_rgba(0,0,0,0.2)]">
                                <span className="font-extrabold text-sm md:text-base text-white tracking-widest uppercase">
                                    {matchData.match_info?.summary ?? matchData.winner}
                                </span>
                            </div>
                        </div>

                        {/* Scorecards */}
                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                            {[matchData.innings1, matchData.innings2].filter(Boolean).map((inn: any, i: number) => (
                                <div key={i} className="espn-card">
                                    <div className="espn-card-header bg-[#111827] sticky top-0 z-10 flex justify-between items-center">
                                        <span className="text-lg text-[var(--color-espn-secondary)]">{inn.batting_team} INNINGS</span>
                                        <span className="font-mono text-white text-lg">{inn.score}/{inn.wickets} <span className="text-xs text-gray-500 ml-2">({inn.overs_completed} Ov)</span></span>
                                    </div>

                                    {/* Batting Table */}
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm text-left whitespace-nowrap">
                                            <thead className="bg-[#0B1724] text-[var(--color-espn-text-secondary)] border-b border-[var(--color-espn-border)] text-xs font-bold uppercase tracking-wider">
                                                <tr>
                                                    <th className="px-5 py-3">Batter</th>
                                                    <th className="px-2 py-3 w-[25%] font-medium"></th>
                                                    <th className="px-3 py-3 text-right text-white">R</th>
                                                    <th className="px-3 py-3 text-right">B</th>
                                                    <th className="px-3 py-3 text-right">4s</th>
                                                    <th className="px-3 py-3 text-right">6s</th>
                                                    <th className="px-3 py-3 text-right">SR</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-[var(--color-espn-border)] bg-[#1F2937]">
                                                {(inn.batter_scorecards ?? []).map((b: any, bIdx: number) => (
                                                    <tr key={bIdx} className="hover:bg-white/5 transition-colors">
                                                        <td className="px-5 py-3 font-bold text-[#1E88E5]">{b.name}</td>
                                                        <td className="px-2 py-3 text-[11px] text-gray-400 truncate max-w-[150px]">{b.dismissal}</td>
                                                        <td className="px-3 py-3 text-right font-black text-white text-base">{b.runs}</td>
                                                        <td className="px-3 py-3 text-right text-gray-400 font-mono">{b.balls_faced}</td>
                                                        <td className="px-3 py-3 text-right text-gray-400 font-mono">{b.fours}</td>
                                                        <td className="px-3 py-3 text-right text-gray-400 font-mono">{b.sixes}</td>
                                                        <td className="px-3 py-3 text-right text-[var(--color-espn-text-secondary)] font-mono">{b.strike_rate}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>

                                    {/* Bowling Table */}
                                    <div className="overflow-x-auto border-t-4 border-[#0B1724]">
                                        <table className="w-full text-sm text-left whitespace-nowrap">
                                            <thead className="bg-[#0B1724] text-[var(--color-espn-text-secondary)] border-b border-[var(--color-espn-border)] text-xs font-bold uppercase tracking-wider">
                                                <tr>
                                                    <th className="px-5 py-3">Bowler</th>
                                                    <th className="px-3 py-3 text-right">O</th>
                                                    <th className="px-3 py-3 text-right">R</th>
                                                    <th className="px-3 py-3 text-right text-white">W</th>
                                                    <th className="px-3 py-3 text-right">ECON</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-[var(--color-espn-border)] bg-[#1F2937]">
                                                {(inn.bowler_figures ?? []).map((b: any, bIdx: number) => (
                                                    <tr key={bIdx} className="hover:bg-white/5 transition-colors">
                                                        <td className="px-5 py-3 font-bold text-[#1E88E5]">{b.name}</td>
                                                        <td className="px-3 py-3 text-right text-gray-400 font-mono">{b.overs}</td>
                                                        <td className="px-3 py-3 text-right text-gray-400 font-mono">{b.runs_conceded}</td>
                                                        <td className="px-3 py-3 text-right font-black text-white text-base">{b.wickets}</td>
                                                        <td className="px-3 py-3 text-right text-[var(--color-espn-text-secondary)] font-mono">{b.economy}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Fall of Wickets Feed */}
                        <div className="espn-card">
                            <div className="espn-card-header bg-[#111827]">
                                <div className="flex items-center gap-2">
                                    <AlertCircle className="w-5 h-5 text-red-500" />
                                    Fall of Wickets Tracker
                                </div>
                            </div>
                            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-10 bg-[#0B1724] bg-opacity-50">
                                {[matchData.innings1, matchData.innings2].filter(Boolean).map((inn: any, i: number) => (
                                    <div key={i} className="relative">
                                        <h3 className="text-sm font-black text-[var(--color-espn-text-secondary)] uppercase tracking-widest mb-4 flex items-center gap-2 sticky top-0 bg-[#0B1724] py-2 z-10 border-b border-white/5">
                                            <ArrowRight className="w-4 h-4 text-[var(--color-espn-primary)]" />
                                            {inn.batting_team} Wickets
                                        </h3>

                                        <div className="space-y-4 pl-2 border-l-2 border-[#1F2937] ml-2 pb-2">
                                            {(inn.wicket_timeline ?? []).length === 0 ? (
                                                <div className="text-sm text-gray-500 italic pl-4 py-2">No wickets fell during this innings</div>
                                            ) : (
                                                (inn.wicket_timeline ?? []).map((w: any, wIdx: number) => (
                                                    <motion.div
                                                        key={wIdx}
                                                        initial={{ opacity: 0, x: -20 }}
                                                        animate={{ opacity: 1, x: 0 }}
                                                        transition={{ delay: wIdx * 0.1, type: "spring", stiffness: 100 }}
                                                        className="relative flex items-center gap-4 text-sm bg-[#1F2937] p-3 rounded-lg border border-white/5 shadow-md group hover:border-[#1E88E5]/50 transition-colors ml-4"
                                                    >
                                                        <div className="absolute -left-[27px] top-1/2 -translate-y-1/2 w-4 h-4 bg-[#111827] rounded-full border-2 border-red-500 z-10"></div>
                                                        <div className="absolute -left-4 top-1/2 -translate-y-1/2 w-4 h-0.5 bg-[#1F2937]"></div>

                                                        <div className="flex flex-col items-center justify-center bg-[#0B1724] text-gray-400 px-3 py-1.5 rounded-md border border-[var(--color-espn-border)] min-w-[3.5rem] font-mono shadow-inner">
                                                            <span className="text-[10px] font-bold tracking-widest leading-none mb-1 opacity-70">OVER</span>
                                                            <span className="leading-none text-white">{w.over}.{w.ball}</span>
                                                        </div>

                                                        <div className="flex-1">
                                                            <div className="font-extrabold text-white text-base tracking-tight group-hover:text-[#1E88E5] transition-colors">{w.batter_out}</div>
                                                            <div className="text-xs text-[var(--color-espn-text-secondary)] font-medium mt-0.5">
                                                                FOW: <span className="text-red-400 font-bold ml-1">{w.score}-{w.wicket_number}</span>
                                                            </div>
                                                        </div>
                                                    </motion.div>
                                                ))
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
