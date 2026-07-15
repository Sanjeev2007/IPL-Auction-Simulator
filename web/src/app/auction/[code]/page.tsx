"use client";

/**
 * Room orchestrator. Reads this browser's saved seat for {code}, opens the
 * WebSocket, and renders the right screen for the room phase: lobby → live
 * bidding → complete. If there's no saved seat (e.g. a shared link), it sends
 * the visitor back to the landing form to join with the code.
 */

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, RadioTower } from "lucide-react";
import { EmptyState } from "@/components/ui";
import { StatusDot } from "@/components/auction/pieces";
import { Lobby } from "@/components/auction/Lobby";
import { LiveBidding } from "@/components/auction/LiveBidding";
import { Complete } from "@/components/auction/Complete";
import { useAuctionSocket } from "@/hooks/useAuctionSocket";
import { loadCreds, type Creds } from "@/lib/auction";

export default function AuctionRoomPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = use(params);
  const roomCode = code.toUpperCase();
  const router = useRouter();

  // Creds live in localStorage → read after mount to stay SSR-safe.
  const [creds, setCreds] = useState<Creds | null>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    setCreds(loadCreds(roomCode));
    setReady(true);
  }, [roomCode]);

  const { state, start, placeBid, next } = useAuctionSocket(roomCode, creds?.token ?? null);

  if (ready && !creds) {
    return (
      <EmptyState title="Join this room" meta={roomCode}>
        <p className="mb-4">
          You don&apos;t have a seat in room{" "}
          <span className="font-mono text-faint">{roomCode}</span> on this device.
        </p>
        <button className="cta-accent px-4 py-2" onClick={() => router.push("/auction")}>
          Go to the join screen
        </button>
      </EmptyState>
    );
  }

  if (!ready || !creds) {
    return <div className="py-16 text-center font-mono text-[12px] text-faint">Loading room…</div>;
  }

  const connected = state.status === "open";

  return (
    <div>
      {/* Room header strip */}
      <div className="mb-[18px] flex items-center justify-between gap-4 border-b border-edge-soft pb-[14px]">
        <div className="flex items-center gap-3">
          <Link
            href="/auction"
            className="flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-[0.08em] text-faint transition-colors hover:text-muted"
          >
            <ArrowLeft className="h-[13px] w-[13px]" /> Exit
          </Link>
          <span className="text-edge">/</span>
          <span className="font-mono text-[13px] tracking-[0.14em] text-ink">{roomCode}</span>
        </div>
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.08em] text-faint">
          <RadioTower className="h-[13px] w-[13px]" />
          <StatusDot ok={connected} />
          {connected ? "connected" : state.status === "connecting" ? "connecting…" : "reconnecting…"}
          <span className="text-edge">·</span>
          <span>{state.phase.replace("_", " ")}</span>
        </div>
      </div>

      {state.phase === "lobby" && <Lobby state={state} me={creds} onStart={() => start()} />}
      {state.phase === "in_progress" && (
        <LiveBidding state={state} me={creds} onBid={placeBid} onNext={next} />
      )}
      {state.phase === "complete" && <Complete state={state} me={creds} />}
    </div>
  );
}
