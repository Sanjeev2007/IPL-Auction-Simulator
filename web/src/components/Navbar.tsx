"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Trophy, BarChart3, Home, Zap } from "lucide-react";
import { clsx } from "clsx";

export default function Navbar() {
    const pathname = usePathname();

    const navLinks = [
        { name: "Home", href: "/", icon: Home },
        { name: "Live Simulator", href: "/simulator", icon: Activity },
        { name: "Tournament Standings", href: "/tournament", icon: Trophy },
        { name: "Global Analytics", href: "/analytics", icon: BarChart3 },
    ];

    return (
        <div className="sticky top-0 z-50 flex flex-col shadow-xl">
            {/* Main Navbar */}
            <nav className="bg-[#111827] text-white border-b border-white/5">
                <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        <div className="flex-shrink-0 flex items-center space-x-3">
                            <div className="bg-[#1E88E5] p-2 rounded-lg">
                                <Trophy className="h-5 w-5 text-white" />
                            </div>
                            <span className="font-extrabold text-xl tracking-tight hidden sm:block">
                                IPL<span className="text-[#1E88E5]">SIM</span>PRO
                            </span>
                            <span className="font-extrabold text-xl tracking-tight sm:hidden">
                                IPL<span className="text-[#1E88E5]">SIM</span>
                            </span>
                        </div>

                        <div className="flex space-x-1 sm:space-x-2">
                            {navLinks.map((link) => {
                                const Icon = link.icon;
                                const isActive = pathname === link.href;

                                return (
                                    <Link
                                        key={link.name}
                                        href={link.href}
                                        className={clsx(
                                            "flex items-center space-x-2 px-3 py-2 rounded-md font-semibold text-sm transition-all duration-200",
                                            isActive
                                                ? "bg-[#1E88E5]/10 text-[#1E88E5]"
                                                : "text-gray-400 hover:bg-white/5 hover:text-gray-200"
                                        )}
                                    >
                                        <Icon className="h-4 w-4" />
                                        <span className="hidden md:block">{link.name}</span>
                                    </Link>
                                );
                            })}
                        </div>
                    </div>
                </div>
            </nav>

            {/* Live Ticker Feed */}
            <div className="bg-[#1E88E5] text-white h-8 overflow-hidden flex items-center shadow-inner relative">
                <div className="absolute left-0 top-0 bottom-0 bg-[#0d47a1] px-4 flex items-center z-10 font-bold text-xs uppercase tracking-wider space-x-2 shadow-lg">
                    <Zap className="w-3 h-3 fill-white" />
                    <span>Live Updates</span>
                </div>
                <div className="whitespace-nowrap flex pl-[140px] animate-[ticker_30s_linear_infinite] group hover:[animation-play-state:paused] text-sm items-center space-x-12 font-medium">
                    <span className="flex items-center space-x-2"><span className="text-white/70 font-bold">IPL SIM:</span> <span>CSK needed 18 off the last over, Sky hits 3 sixes!</span></span>
                    <span className="flex items-center space-x-2"><span className="text-white/70 font-bold">RESULT:</span> <span>MI (182/4) def KKR (175/8) by 7 runs. POTM: Boom Boom (4-21)</span></span>
                    <span className="flex items-center space-x-2"><span className="text-white/70 font-bold">TOURNAMENT:</span> <span>KKR odds jump to 48% after 3 consecutive simulated wins.</span></span>
                    <span className="flex items-center space-x-2"><span className="text-white/70 font-bold">STAT ALERT:</span> <span>Jos Buttler crosses 73.9 Batting Rating in latest simulation tier.</span></span>
                    <span className="flex items-center space-x-2"><span className="text-white/70 font-bold">IPL SIM:</span> <span>CSK needed 18 off the last over, Sky hits 3 sixes!</span></span>
                    <span className="flex items-center space-x-2"><span className="text-white/70 font-bold">RESULT:</span> <span>MI (182/4) def KKR (175/8) by 7 runs. POTM: Boom Boom (4-21)</span></span>
                </div>
            </div>
        </div>
    );
}
