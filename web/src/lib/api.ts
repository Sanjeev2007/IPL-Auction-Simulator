/**
 * API client for the IPL Auction Simulator FastAPI backend.
 *
 * The backend exposes real `/api/*` routes (see `src/api/server.py`). This module
 * is the single place that knows those routes and their response shapes, adapting
 * each into the field names the pages actually consume. Pages import from here and
 * never touch `fetch`/route strings directly.
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

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
  /** Percentage 0–100; 0 when the backend has no tournament results yet. */
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
/* Fetchers                                                            */
/* ------------------------------------------------------------------ */

/** Team strengths for the Home "Team Strength Index" table. */
export async function fetchTeamStats(): Promise<TeamStat[]> {
  try {
    const res = await fetch(`${API_BASE}/api/team_stats`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return (data.teams ?? []).map(
      (t: {
        team_id: string;
        team_name?: string;
        batting_strength: number;
        bowling_strength: number;
        overall_strength: number;
      }): TeamStat => ({
        team_id: t.team_id,
        name: t.team_name ?? t.team_id,
        batting_strength: t.batting_strength,
        bowling_strength: t.bowling_strength,
        overall_strength: t.overall_strength,
      })
    );
  } catch {
    return [];
  }
}

/** Championship odds for the Home "To Win Championship" panel. */
export async function fetchChampionshipOdds(): Promise<ChampionshipOdd[]> {
  try {
    const res = await fetch(`${API_BASE}/api/championship_odds`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    const data = await res.json();
    return (data.odds ?? []).map(
      (t: {
        team_id: string;
        team_name?: string;
        championship_probability: number;
        finals_probability: number;
      }): ChampionshipOdd => ({
        team_id: t.team_id,
        name: t.team_name ?? t.team_id,
        championship_probability: t.championship_probability,
        final_probability: t.finals_probability,
      })
    );
  } catch {
    return [];
  }
}

/** Projected points table for the Tournament page. */
export async function fetchPointsTable(): Promise<PointsRow[]> {
  try {
    const res = await fetch(`${API_BASE}/api/points_table`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    const data = await res.json();
    return (data.points_table ?? []).map(
      (t: {
        rank: number;
        team_id: string;
        team_name?: string;
        average_points: number;
        playoff_probability?: number;
      }): PointsRow => ({
        rank: t.rank,
        team_id: t.team_id,
        name: t.team_name ?? t.team_id,
        points: t.average_points,
        playoff_probability: t.playoff_probability ?? 0,
      })
    );
  } catch {
    return [];
  }
}

/**
 * Simulate a single match between two teams via `POST /api/simulate_match`.
 * One call returns the full scorecard — no separate play_next/scorecard step.
 */
export async function simulateMatch(
  team1Id: string,
  team2Id: string
): Promise<MatchResult> {
  const res = await fetch(`${API_BASE}/api/simulate_match`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ team1_id: team1Id, team2_id: team2Id }),
    cache: "no-store",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Simulation failed.");
  }
  return res.json();
}

/**
 * Pick two distinct teams at random and simulate a match between them.
 * Used by the Simulator (on click) and Analytics (on load / re-simulate),
 * both of which show a one-off match rather than a fixed fixture.
 */
export async function simulateRandomMatch(): Promise<MatchResult> {
  const teams = await fetchTeamStats();
  if (teams.length < 2) {
    throw new Error("Not enough teams available to simulate a match.");
  }
  const first = Math.floor(Math.random() * teams.length);
  let second = Math.floor(Math.random() * (teams.length - 1));
  if (second >= first) second += 1; // ensure distinct from `first`
  return simulateMatch(teams[first].team_id, teams[second].team_id);
}
