"use client";

/** Pre-auction lobby: share the code, watch people join, host starts. */

import { useState } from "react";
import { clsx } from "clsx";
import { Check, Copy, Crown, Play, Users } from "lucide-react";
import { Panel } from "@/components/ui";
import { StatusDot } from "@/components/auction/pieces";
import type { LiveState } from "@/hooks/useAuctionSocket";
import { formatINR, type Creds } from "@/lib/auction";

export function Lobby({
  state,
  me,
  onStart,
}: {
  state: LiveState;
  me: Creds;
  onStart: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const canStart = me.is_host && state.participants.length >= 2;

  async function copy() {
    try {
      await navigator.clipboard.writeText(state.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    } catch {
      /* clipboard may be blocked; the code is shown on screen anyway */
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
      {/* Participants */}
      <Panel
        title="Lobby"
        right={
          <span className="flex items-center gap-2 font-mono text-[11px] text-faint">
            <Users className="h-[13px] w-[13px]" /> {state.participants.length} JOINED
          </span>
        }
      >
        <ul className="divide-y divide-edge-soft">
          {state.participants.map((p) => {
            const connected = state.presence[p.id] !== false;
            const isMe = p.id === me.participant_id;
            return (
              <li key={p.id} className="flex items-center justify-between gap-3 py-3">
                <div className="flex items-center gap-3">
                  <StatusDot ok={connected} title={connected ? "connected" : "reconnecting"} />
                  <span className="text-[14px] font-semibold text-ink">{p.display_name}</span>
                  {p.is_host && <Crown className="h-[13px] w-[13px] text-warm" aria-label="host" />}
                  {isMe && (
                    <span className="rounded-[3px] border border-accent/40 px-1.5 py-[1px] font-mono text-[9px] uppercase tracking-[0.08em] text-accent">
                      you
                    </span>
                  )}
                </div>
                <span className="font-mono tnum text-[12.5px] text-faint">
                  {formatINR(p.budget_remaining)}
                </span>
              </li>
            );
          })}
          {state.participants.length < 2 && (
            <li className="py-6 text-center text-[13px] text-muted">
              Waiting for at least one more player to join…
            </li>
          )}
        </ul>
      </Panel>

      {/* Share + start */}
      <div className="space-y-4">
        <Panel title="Room Code" meta="SHARE TO INVITE">
          <div className="pt-1">
            <button
              onClick={copy}
              className="group flex w-full items-center justify-between gap-3 rounded-md border border-edge bg-bg px-4 py-3 transition-colors hover:border-faint"
            >
              <span className="font-mono text-[30px] font-semibold tracking-[0.22em] text-ink">
                {state.code}
              </span>
              <span className="flex items-center gap-1.5 font-mono text-[11px] text-faint group-hover:text-muted">
                {copied ? <Check className="h-4 w-4 text-accent" /> : <Copy className="h-4 w-4" />}
                {copied ? "copied" : "copy"}
              </span>
            </button>
            <p className="mt-3 text-[12px] leading-relaxed text-muted">
              Others join at <span className="font-mono text-faint">/auction</span> with this code.
            </p>
          </div>
        </Panel>

        <Panel title="Start" meta={me.is_host ? "HOST CONTROL" : "HOST ONLY"}>
          <div className="pt-1">
            {me.is_host ? (
              <>
                <button
                  onClick={onStart}
                  disabled={!canStart}
                  className={clsx("cta-accent w-full px-4 py-3 text-[14px]")}
                >
                  <Play className="h-4 w-4" />
                  Start auction
                </button>
                {!canStart && (
                  <p className="mt-2.5 text-center text-[12px] text-faint">
                    Need at least 2 players to start.
                  </p>
                )}
              </>
            ) : (
              <p className="py-2 text-center text-[13px] text-muted">
                Waiting for the host to start the auction…
              </p>
            )}
          </div>
        </Panel>
      </div>
    </div>
  );
}
