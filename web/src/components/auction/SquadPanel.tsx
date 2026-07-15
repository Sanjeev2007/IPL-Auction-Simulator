"use client";

/** One participant's live panel: budget, squad progress, and drafted players. */

import { clsx } from "clsx";
import { Crown, Wifi, WifiOff } from "lucide-react";
import { RatingPip } from "@/components/auction/pieces";
import { formatINR, type ParticipantT, type RoomConfigT } from "@/lib/auction";

export function SquadPanel({
  p,
  config,
  isMe,
  isLeading,
  connected,
}: {
  p: ParticipantT;
  config: RoomConfigT | null;
  isMe: boolean;
  isLeading?: boolean;
  connected?: boolean;
}) {
  const max = config?.squad_max ?? 15;
  const min = config?.squad_min ?? 11;
  return (
    <div
      className={clsx(
        "rounded-md border bg-surface p-3 transition-colors",
        isLeading ? "border-accent/50" : "border-edge"
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          {connected === false ? (
            <WifiOff className="h-[13px] w-[13px] shrink-0 text-faint" />
          ) : (
            <Wifi className="h-[13px] w-[13px] shrink-0 text-accent" />
          )}
          <span className="truncate text-[13.5px] font-semibold text-ink">{p.display_name}</span>
          {p.is_host && <Crown className="h-[12px] w-[12px] shrink-0 text-warm" aria-label="host" />}
          {isMe && (
            <span className="rounded-[3px] border border-accent/40 px-1 py-[1px] font-mono text-[9px] uppercase tracking-[0.08em] text-accent">
              you
            </span>
          )}
        </div>
        <span className="shrink-0 font-mono tnum text-[13px] text-ink">
          {formatINR(p.budget_remaining)}
        </span>
      </div>

      <div className="mt-2 flex items-center gap-2">
        <div className="h-[4px] flex-1 overflow-hidden rounded-full bg-elevated">
          <div
            className="h-full rounded-full bg-accent/70"
            style={{ width: `${Math.min(100, (p.squad_size / max) * 100)}%` }}
          />
        </div>
        <span className="font-mono tnum text-[11px] text-faint">
          {p.squad_size}/{max}
          {p.squad_size >= min ? "" : ` · need ${min}`}
        </span>
      </div>

      {p.squad.length > 0 && (
        <ul className="mt-2 max-h-[168px] space-y-[3px] overflow-y-auto pr-1">
          {p.squad.map((e) => (
            <li key={e.player.player_id} className="flex items-center justify-between gap-2 text-[12.5px]">
              <span className="truncate text-muted">{e.player.name}</span>
              <span className="flex shrink-0 items-center gap-2">
                <RatingPip value={e.player.overall_rating} />
                <span className="w-[52px] text-right font-mono tnum text-[12px] text-faint">
                  {formatINR(e.price)}
                </span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
