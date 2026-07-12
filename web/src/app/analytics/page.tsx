"use client";

import { useEffect, useState } from "react";
import {
    LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";
import { BarChart3, RefreshCw, TrendingUp } from "lucide-react";
import { simulateRandomMatch, type MatchResult } from "@/lib/api";
import { buildManhattanData, buildWormData } from "@/lib/transforms";

export default function AnalyticsPage() {
    const [data, setData] = useState<MatchResult | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchScorecard = async () => {
        setLoading(true);
        try {
            const js = await simulateRandomMatch();
            setData(js);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchScorecard();
    }, []);

    if (loading) {
        return (
            <div className="h-[60vh] flex flex-col justify-center items-center gap-4">
                <RefreshCw className="w-10 h-10 animate-spin text-[var(--color-espn-primary)]" />
                <span className="text-[var(--color-espn-text-secondary)] font-bold tracking-widest text-sm animate-pulse">GENERATING MATCH DATA</span>
            </div>
        );
    }
    if (!data || !data.innings1 || !data.innings2) return <div className="text-red-500 font-bold p-10 text-center">No match data yet — start the league and play a match first.</div>;

    // Process data for charts
    const team1 = data.match_info.team1;
    const team2 = data.match_info.team2;

    const manhattanData = buildManhattanData(data, team1, team2); // runs per over
    const wormData = buildWormData(data, team1, team2); // cumulative runs per over

    return (
        <div className="space-y-6 pb-12">
            <div className="bg-[#111827] border border-[var(--color-espn-border)] p-6 rounded-xl shadow-lg flex flex-col sm:flex-row justify-between items-center gap-4 relative isolate overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-[#1E88E5]/5 to-transparent pointer-events-none"></div>
                <div className="relative z-10 flex items-center gap-4">
                    <div className="bg-[#1F2937] p-3 rounded-lg border border-white/5 shadow-inner">
                        <BarChart3 className="w-6 h-6 text-[var(--color-espn-primary)]" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-white tracking-tight">Global Match Analytics</h2>
                        <p className="text-xs font-bold text-[var(--color-espn-text-secondary)] uppercase tracking-widest mt-1">Data Modeling Tool</p>
                    </div>
                </div>
                <button
                    onClick={fetchScorecard}
                    className="relative z-10 flex items-center gap-2 px-5 py-2.5 bg-[#1F2937] hover:bg-[#374151] hover:text-white text-gray-300 font-bold rounded-lg border border-[var(--color-espn-border)] transition-colors shadow-sm"
                >
                    <RefreshCw className="w-4 h-4" /> RE-SIMULATE MATCH
                </button>
            </div>

            <div className="bg-gradient-to-r from-[var(--color-espn-secondary)] to-orange-600 text-white p-4 rounded-xl shadow-[0_4px_20px_rgba(245,158,11,0.2)] border border-orange-400 flex flex-col items-center justify-center text-center">
                <div className="font-extrabold text-sm uppercase tracking-widest mb-1 opacity-90 text-orange-100 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" /> Result Summary
                </div>
                <div className="font-black text-xl md:text-2xl drop-shadow-md">{data.match_info.summary}</div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                {/* Manhattan Chart: Bar Graph runs per over */}
                <div className="espn-card group">
                    <div className="espn-card-header bg-[#111827]">
                        <div className="flex items-center gap-2 text-[var(--color-espn-text-secondary)]">
                            <span className="w-2 h-2 rounded-full bg-[var(--color-espn-secondary)]"></span>
                            Manhattan Chart
                        </div>
                    </div>
                    <div className="p-6 h-[400px] bg-[#0B1724]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={manhattanData} margin={{ top: 20, right: 10, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="over" tick={{ fill: '#9CA3AF', fontSize: 11, fontWeight: 700 }} axisLine={false} tickLine={false} dy={10} />
                                <YAxis tick={{ fill: '#9CA3AF', fontSize: 11, fontWeight: 700 }} axisLine={false} tickLine={false} />
                                <Tooltip
                                    cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                                    contentStyle={{ backgroundColor: '#1F2937', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontWeight: 700, boxShadow: '0 10px 25px -5px rgba(0,0,0,0.5)' }}
                                />
                                <Legend wrapperStyle={{ paddingTop: '20px' }} iconType="circle" />
                                <Bar dataKey={team1} fill="var(--color-espn-secondary)" radius={[4, 4, 0, 0]} maxBarSize={20} />
                                <Bar dataKey={team2} fill="var(--color-espn-primary)" radius={[4, 4, 0, 0]} maxBarSize={20} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Worm Chart: Cumulative Graph runs per over */}
                <div className="espn-card group">
                    <div className="espn-card-header bg-[#111827]">
                        <div className="flex items-center gap-2 text-[var(--color-espn-text-secondary)]">
                            <span className="w-2 h-2 rounded-full bg-[var(--color-espn-primary)]"></span>
                            Worm Chart (Cumulative)
                        </div>
                    </div>
                    <div className="p-6 h-[400px] bg-[#0B1724]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={wormData} margin={{ top: 20, right: 10, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="over" tick={{ fill: '#9CA3AF', fontSize: 11, fontWeight: 700 }} axisLine={false} tickLine={false} dy={10} />
                                <YAxis tick={{ fill: '#9CA3AF', fontSize: 11, fontWeight: 700 }} axisLine={false} tickLine={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1F2937', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontWeight: 700, boxShadow: '0 10px 25px -5px rgba(0,0,0,0.5)' }}
                                />
                                <Legend wrapperStyle={{ paddingTop: '20px' }} iconType="plainline" />
                                <Line type="monotone" dataKey={team1} stroke="var(--color-espn-secondary)" strokeWidth={4} dot={{ r: 4, strokeWidth: 2, fill: '#1F2937' }} activeDot={{ r: 7, strokeWidth: 0 }} />
                                <Line type="monotone" dataKey={team2} stroke="var(--color-espn-primary)" strokeWidth={4} dot={{ r: 4, strokeWidth: 2, fill: '#1F2937' }} activeDot={{ r: 7, strokeWidth: 0 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

            </div>
        </div>
    );
}
