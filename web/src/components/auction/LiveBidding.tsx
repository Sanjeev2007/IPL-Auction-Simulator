"use client";

/**
 * The live bidding screen — the hero. Current player card with heat-encoded
 * ratings, the standing bid, a live countdown, your budget, the Bid control
 * (tiered increment + optional jump), per-participant squads, and a bid log.
 */

import { clsx } from "clsx";
import { Gavel, SkipForward, TriangleAlert } from "lucide-react";
import { Panel } from "@/components/ui";
import { Rating, TimerBar, GhostButton } from "@/components/auction/pieces";
import { SquadPanel } from "@/components/auction/SquadPanel";
import type { LiveState } from "@/hooks/useAuctionSocket";
import { formatINR, type Creds } from "@/lib/auction";

export function LiveBidding({
  state,
  me,
  onBid,
  onNext,
}: {
  state: LiveState;
  me: Creds;
  onBid: (amount: number) => void;
  onNext: () => void;
}) {
  const cfg = state.config;
  const lot = state.activeLot;
  const you = state.participants.find((p) => p.id === me.participant_id);
  const yourBudget = you?.budget_remaining ?? cfg?.starting_budget ?? 0;
  const squadFull = !!you && !!cfg && you.squad_size >= cfg.squad_max;

  const min = state.minNextBid;
  const currentBid = lot?.currentBid ?? null;
  const topBidder = state.participants.find((p) => p.id === lot?.currentBidderId);
  const youAreTop = lot?.currentBidderId === me.participant_id;
  const canAfford = min != null && min <= yourBudget;
  const canBid = !!lot && min != null && !youAreTop && canAfford && !squadFull;

  const step = currentBid != null && min != null ? min - currentBid : null;
  const jumpAmount = step != null && min != null ? min + step : null;
  const canJump = jumpAmount != null && jumpAmount <= yourBudget && canBid;

  const errFresh = state.lastError && Date.now() - state.lastError.at < 4000;

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
      {/* ── Main column ──────────────────────────────────────────────── */}
      <div className="space-y-4">
        <Panel
          title="On the Block"
          meta={
            lot
              ? `LOT ${lot.index + 1} · ${state.lotsRemaining} LEFT`
              : "WAITING FOR NEXT LOT"
          }
        >
          {lot ? (
            <div className="pt-1">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="min-w-0">
                  <h2 className="font-display text-[34px] font-semibold leading-none tracking-tight">
                    {lot.player.name}
                  </h2>
                  <div className="mt-2.5 flex flex-wrap items-center gap-2 font-mono text-[11px] uppercase tracking-[0.06em] text-muted">
                    <span className="rounded-[3px] border border-edge bg-elevated px-2 py-[3px]">
                      {lot.player.role}
                    </span>
                    {lot.player.country && lot.player.country !== "Unknown" && (
                      <span className="text-faint">{lot.player.country}</span>
                    )}
                    {lot.player.is_wicketkeeper && <span className="text-faint">· keeper</span>}
                    {lot.player.can_bowl && <span className="text-faint">· bowls</span>}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono text-[10px] uppercase tracking-[0.09em] text-faint">
                    Base price
                  </div>
                  <div className="mt-1 font-mono tnum text-[20px] text-ink">
                    {formatINR(lot.player.base_price)}
                  </div>
                </div>
              </div>

              <div className="mt-5 flex items-center gap-8 border-t border-edge-soft pt-4">
                <Rating label="Bat" value={lot.player.bat_rating} />
                <Rating label="Bowl" value={lot.player.bowl_rating} />
                <Rating label="Overall" value={lot.player.overall_rating} />
              </div>
            </div>
          ) : (
            <div className="py-10 text-center text-[13px] text-muted">
              Resolving the lot…
            </div>
          )}
        </Panel>

        {/* Bid + timer + controls */}
        <Panel title="Bidding" meta={youAreTop ? "YOU LEAD" : ""}>
          <div className="grid gap-5 pt-1 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
            <div>
              <div className="font-mono text-[10.5px] uppercase tracking-[0.1em] text-faint">
                Current bid
              </div>
              <div
                className={clsx(
                  "mt-1 font-mono tnum text-[38px] font-semibold leading-none",
                  currentBid != null ? "text-ink" : "text-faint"
                )}
              >
                {currentBid != null ? formatINR(currentBid) : "—"}
              </div>
              <div className="mt-2 text-[12.5px] text-muted">
                {currentBid != null && topBidder ? (
                  <>
                    held by{" "}
                    <span className={clsx("font-semibold", youAreTop ? "text-accent" : "text-ink")}>
                      {topBidder.display_name}
                    </span>
                  </>
                ) : (
                  "No bids yet — open at base price."
                )}
              </div>
            </div>

            <div className="flex flex-col justify-center">
              <TimerBar deadlineMs={state.deadlineMs} totalSeconds={state.timerSeconds} />
            </div>
          </div>

          <div className="mt-5 flex flex-col gap-3 border-t border-edge-soft pt-4 sm:flex-row sm:items-end sm:justify-between sm:gap-4">
            <div>
              <div className="font-mono text-[10.5px] uppercase tracking-[0.1em] text-faint">
                Your budget
              </div>
              <div className="mt-1 font-mono tnum text-[22px] font-medium text-ink">
                {formatINR(yourBudget)}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2.5">
              {me.is_host && (
                <GhostButton onClick={onNext} title="Force-close this lot now">
                  <SkipForward className="h-4 w-4" /> Next
                </GhostButton>
              )}
              {canJump && jumpAmount != null && (
                <GhostButton onClick={() => onBid(jumpAmount)}>
                  Jump {formatINR(jumpAmount)}
                </GhostButton>
              )}
              <button
                onClick={() => min != null && onBid(min)}
                disabled={!canBid}
                className="cta-accent flex-1 px-5 py-3 text-[15px] sm:flex-none sm:py-2.5 sm:text-[14px]"
              >
                <Gavel className="h-4 w-4" />
                {min != null ? `Bid ${formatINR(min)}` : "Bid"}
              </button>
            </div>
          </div>

          {/* Contextual reason the Bid button is disabled / last rejection */}
          {(errFresh || (!canBid && lot)) && (
            <div className="mt-3 flex items-center gap-2 font-mono text-[11.5px] text-[color:var(--color-warm)]">
              <TriangleAlert className="h-[13px] w-[13px]" />
              {errFresh
                ? state.lastError!.message
                : youAreTop
                ? "You're the highest bidder."
                : squadFull
                ? "Your squad is full."
                : !canAfford
                ? "Not enough budget for the next bid."
                : ""}
            </div>
          )}
        </Panel>
      </div>

      {/* ── Side column: squads + bid log ────────────────────────────── */}
      <div className="space-y-4">
        <Panel title="Squads" meta="BUDGET · DRAFTED" bodyClassName="space-y-2.5 pt-1">
          {state.participants.map((p) => (
            <SquadPanel
              key={p.id}
              p={p}
              config={cfg}
              isMe={p.id === me.participant_id}
              isLeading={p.id === lot?.currentBidderId}
              connected={state.presence[p.id] !== false}
            />
          ))}
        </Panel>

        <Panel title="Bid Log" meta="LIVE">
          <ul className="max-h-[280px] space-y-[6px] overflow-y-auto pt-1 font-mono text-[12px]">
            {state.bidLog.length === 0 && (
              <li className="py-3 text-center text-faint">No bids yet.</li>
            )}
            {state.bidLog.map((l) => (
              <li key={l.id} className="flex items-center justify-between gap-2">
                {l.kind === "sold" ? (
                  <>
                    <span className="truncate text-accent">
                      ✓ {l.actorName} won {l.playerName}
                    </span>
                    <span className="shrink-0 tnum text-accent">{l.amountDisplay}</span>
                  </>
                ) : l.kind === "unsold" ? (
                  <span className="truncate text-faint">— {l.playerName} unsold</span>
                ) : (
                  <>
                    <span className="truncate text-muted">{l.actorName}</span>
                    <span className="shrink-0 tnum text-ink">{l.amountDisplay}</span>
                  </>
                )}
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </div>
  );
}
