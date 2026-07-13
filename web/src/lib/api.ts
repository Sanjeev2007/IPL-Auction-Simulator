/**
 * Static data layer for the IPL Auction Simulator.
 *
 * This is a backend-free deploy: the Python engine's output is pre-generated into
 * JSON at build time (see `scripts/build_web_data.py`) and shipped with the site.
 * The small tables are imported directly (used by server components); the match
 * pool is fetched from /public on demand (used by the client Simulator/Analytics).
 * Function signatures match the old FastAPI client, so the pages are unchanged.
 */

import teamStatsJson from "../data/team_stats.json";
import oddsJson from "../data/championship_odds.json";
import pointsJson from "../data/points_table.json";

/* ------------------------------------------------------------------ */
/* Shared types                                                        */
/* ------------------------------------------------------------------ */

/** A team's strength profile (Home → "Team Strength Index"). */
export interface TeamStat {
  team_id: string;
  name: string;
  batting_strength: number;
  bowling_strength: number;
  overall_strength: number;
}

/** Championship odds row (Home → "To Win Championship"). */
export interface ChampionshipOdd {
  team_id: string;
  name: string;
  /** Percentage 0–100. */
  championship_probability: number;
  /** Percentage 0–100 (reaching the final). */
  final_probability: number;
}

/** Projected league-table row (Tournament page). */
export interface PointsRow {
  rank: number;
  team_id: string;
  name: string;
  /** Mean points across the simulated seasons. */
  points: number;
  /** Percentage 0–100. */
  playoff_probability: number;
}

export interface BatterScorecard {
  name: string;
  runs: number;
  balls_faced: number;
  fours: number;
  sixes: number;
  strike_rate: number;
  dismissal: string;
}

export interface BowlerFigure {
  name: string;
  overs: string;
  runs_conceded: number;
  wickets: number;
  economy: number;
}

export interface OverRuns {
  over: number;
  runs: number;
}

export interface WicketEvent {
  wicket_number: number;
  over: number;
  ball: number;
  score: number;
  batter_out: string;
}

export interface Innings {
  batting_team: string;
  bowling_team: string;
  score: number;
  wickets: number;
  overs_completed: number | string;
  batter_scorecards: BatterScorecard[];
  bowler_figures: BowlerFigure[];
  run_rate_by_over: OverRuns[];
  wicket_timeline: WicketEvent[];
}

export interface MatchInfo {
  match_id: string;
  team1: string;
  team2: string;
  winner: string;
  margin: string;
  summary: string;
}

/** Full simulated-match result (Simulator + Analytics pages). */
export interface MatchResult {
  match_info: MatchInfo;
  innings1: Innings | null;
  innings2: Innings | null;
}

/* ------------------------------------------------------------------ */
/* Raw shapes as emitted by scripts/build_web_data.py                  */
/* ------------------------------------------------------------------ */

interface RawTeam {
  team_id: string;
  team_name?: string;
  batting_strength: number;
  bowling_strength: number;
  overall_strength: number;
}
interface RawOdd {
  team_id: string;
  team_name?: string;
  championship_probability: number;
  finals_probability: number;
}
interface RawPointsRow {
  rank: number;
  team_id: string;
  team_name?: string;
  average_points: number;
  playoff_probability?: number;
}

const teamStats = teamStatsJson as { teams: RawTeam[] };
const odds = oddsJson as { odds: RawOdd[] };
const points = pointsJson as { points_table: RawPointsRow[] };

/* ------------------------------------------------------------------ */
/* Data accessors (async to keep the old call sites unchanged)         */
/* ------------------------------------------------------------------ */

/** Team strengths for the Home "Team Strength Index" table. */
export async function fetchTeamStats(): Promise<TeamStat[]> {
  return teamStats.teams.map((t) => ({
    team_id: t.team_id,
    name: t.team_name ?? t.team_id,
    batting_strength: t.batting_strength,
    bowling_strength: t.bowling_strength,
    overall_strength: t.overall_strength,
  }));
}

/** Championship odds for the Home "To Win Championship" panel. */
export async function fetchChampionshipOdds(): Promise<ChampionshipOdd[]> {
  return odds.odds.map((t) => ({
    team_id: t.team_id,
    name: t.team_name ?? t.team_id,
    championship_probability: t.championship_probability,
    final_probability: t.finals_probability,
  }));
}

/** Projected points table for the Tournament page. */
export async function fetchPointsTable(): Promise<PointsRow[]> {
  return points.points_table.map((t) => ({
    rank: t.rank,
    team_id: t.team_id,
    name: t.team_name ?? t.team_id,
    points: t.average_points,
    playoff_probability: t.playoff_probability ?? 0,
  }));
}

/* ------------------------------------------------------------------ */
/* Match pool (client-side; fetched once from /public and cached)      */
/* ------------------------------------------------------------------ */

let matchPool: MatchResult[] | null = null;

async function loadMatchPool(): Promise<MatchResult[]> {
  if (matchPool) return matchPool;
  const res = await fetch("/data/matches.json");
  if (!res.ok) throw new Error("Could not load simulated matches.");
  matchPool = (await res.json()) as MatchResult[];
  return matchPool;
}

function pick<T>(items: T[]): T {
  return items[Math.floor(Math.random() * items.length)];
}

/**
 * Return a pre-simulated match for the chosen matchup. The pool covers every
 * ordered pairing with a few variants, so re-simulating shows real variety.
 */
export async function simulateMatch(
  team1Id: string,
  team2Id: string
): Promise<MatchResult> {
  const pool = await loadMatchPool();
  const forPair = pool.filter(
    (m) => m.match_info.team1 === team1Id && m.match_info.team2 === team2Id
  );
  return pick(forPair.length ? forPair : pool);
}

/** A random pre-simulated match (Analytics on load / re-simulate). */
export async function simulateRandomMatch(): Promise<MatchResult> {
  const pool = await loadMatchPool();
  return pick(pool);
}
