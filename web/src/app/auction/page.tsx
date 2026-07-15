"use client";

/**
 * Auction landing — create a room (host) or join one with a code.
 * On success we persist the participant's token (localStorage, per room) and
 * enter the room route. This is a live client screen talking to the auction
 * backend; it is entirely separate from the static dashboard pages.
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Gavel, Plus, LogIn, Settings2 } from "lucide-react";
import { PageHead, Panel } from "@/components/ui";
import { Reveal } from "@/components/motion";
import { Field, GhostButton } from "@/components/auction/pieces";
import { createRoom, joinRoom, saveCreds, auctionBackendConfigured } from "@/lib/auction";

export default function AuctionLanding() {
  const router = useRouter();

  const [hostName, setHostName] = useState("");
  const [joinName, setJoinName] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [busy, setBusy] = useState<"create" | "join" | null>(null);
  const [error, setError] = useState<string | null>(null);

  // The live auction needs a hosted realtime (WebSocket) backend. On a deployed
  // host with none configured, show an honest notice instead of a form that
  // would fail. Defaults to available so local dev is unaffected.
  const [available, setAvailable] = useState(true);
  useEffect(() => setAvailable(auctionBackendConfigured()), []);

  // Optional host settings (backend already supports these overrides).
  const [showAdv, setShowAdv] = useState(false);
  const [budgetCr, setBudgetCr] = useState("100");
  const [squadMax, setSquadMax] = useState("15");
  const [timer, setTimer] = useState("30");
  const [poolSize, setPoolSize] = useState("");

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!hostName.trim()) return;
    setBusy("create");
    setError(null);
    try {
      const resp = await createRoom({
        display_name: hostName.trim(),
        budget_cr: budgetCr ? Number(budgetCr) : undefined,
        squad_max: squadMax ? Number(squadMax) : undefined,
        timer_seconds: timer ? Number(timer) : undefined,
        pool_size: poolSize ? Number(poolSize) : undefined,
      });
      saveCreds({
        code: resp.room_code,
        participant_id: resp.participant_id,
        token: resp.token,
        is_host: true,
        display_name: hostName.trim(),
      });
      router.push(`/auction/${resp.room_code}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create room.");
      setBusy(null);
    }
  }

  async function handleJoin(e: React.FormEvent) {
    e.preventDefault();
    const code = joinCode.trim().toUpperCase();
    if (!code || !joinName.trim()) return;
    setBusy("join");
    setError(null);
    try {
      const resp = await joinRoom(code, joinName.trim());
      saveCreds({
        code: resp.room_code,
        participant_id: resp.participant_id,
        token: resp.token,
        is_host: resp.is_host,
        display_name: joinName.trim(),
      });
      router.push(`/auction/${resp.room_code}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not join room.");
      setBusy(null);
    }
  }

  return (
    <div>
      <PageHead
        title="Live Auction"
        sub={
          <>
            Draft real players in a live multiplayer auction, then simulate a tournament with the
            squads you build. Create a room and share the code — everyone bids in real time.
          </>
        }
        metaLabel="Mode"
        metaValue="realtime · websocket"
      />

      {error && (
        <Reveal as="div" className="mb-4">
          <div className="rounded-md border border-hot/40 bg-hot/5 px-4 py-3 font-mono text-[12.5px] text-[color:var(--color-hot)]">
            {error}
          </div>
        </Reveal>
      )}

      {!available ? (
        <Reveal as="div">
          <Panel
            title="Hosted auction — coming soon"
            right={<span className="font-mono text-[11px] text-faint">LOCAL ONLY</span>}
          >
            <div className="space-y-3 pt-1 text-[13.5px] leading-relaxed text-muted">
              <p>
                The live multiplayer auction needs a persistent realtime (WebSocket) server, which
                isn&apos;t hosted yet. Everything else here runs backend-free — the auction is the
                one feature that can&apos;t.
              </p>
              <p>
                It&apos;s fully working when you run the project locally: start the API
                (
                <code className="font-mono text-[12px] text-accent">
                  uvicorn src.api.server:app --port 8000
                </code>
                ), run the dashboard, then create a room and share the code.
              </p>
            </div>
          </Panel>
        </Reveal>
      ) : (
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Create */}
        <Reveal as="div">
          <Panel
            title="Create a Room"
            right={
              <span className="flex items-center gap-2 font-mono text-[11px] text-faint">
                <Gavel className="h-[13px] w-[13px] text-accent" /> HOST
              </span>
            }
          >
            <form onSubmit={handleCreate} className="space-y-4 pt-1">
              <Field
                label="Your display name"
                placeholder="e.g. Sanjeev"
                value={hostName}
                maxLength={24}
                onChange={(e) => setHostName(e.target.value)}
                autoComplete="off"
              />

              <button
                type="button"
                onClick={() => setShowAdv((s) => !s)}
                className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.08em] text-faint transition-colors hover:text-muted"
              >
                <Settings2 className="h-[13px] w-[13px]" />
                {showAdv ? "Hide" : "Room"} settings
              </button>

              {showAdv && (
                <div className="grid grid-cols-2 gap-3 rounded-md border border-edge-soft bg-bg/40 p-3">
                  <Field label="Budget (Cr)" type="number" min={1} value={budgetCr} onChange={(e) => setBudgetCr(e.target.value)} />
                  <Field label="Max squad" type="number" min={11} value={squadMax} onChange={(e) => setSquadMax(e.target.value)} />
                  <Field label="Timer (s)" type="number" min={3} value={timer} onChange={(e) => setTimer(e.target.value)} />
                  <Field label="Pool size" type="number" min={2} placeholder="all" value={poolSize} onChange={(e) => setPoolSize(e.target.value)} hint="players up for auction" />
                </div>
              )}

              <button type="submit" disabled={!hostName.trim() || busy === "create"} className="cta-accent w-full px-4 py-2.5 text-[13.5px]">
                <Plus className="h-4 w-4" />
                {busy === "create" ? "Creating…" : "Create room"}
              </button>
            </form>
          </Panel>
        </Reveal>

        {/* Join */}
        <Reveal as="div" delay={0.08}>
          <Panel
            title="Join a Room"
            right={
              <span className="flex items-center gap-2 font-mono text-[11px] text-faint">
                <LogIn className="h-[13px] w-[13px]" /> GUEST
              </span>
            }
          >
            <form onSubmit={handleJoin} className="space-y-4 pt-1">
              <Field
                label="Room code"
                placeholder="e.g. Q5328"
                value={joinCode}
                maxLength={8}
                onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                autoComplete="off"
                className="font-mono uppercase tracking-[0.18em]"
              />
              <Field
                label="Your display name"
                placeholder="e.g. Priya"
                value={joinName}
                maxLength={24}
                onChange={(e) => setJoinName(e.target.value)}
                autoComplete="off"
              />
              <GhostButton type="submit" disabled={!joinCode.trim() || !joinName.trim() || busy === "join"} className="w-full py-2.5">
                <LogIn className="h-4 w-4" />
                {busy === "join" ? "Joining…" : "Join room"}
              </GhostButton>
            </form>
          </Panel>
        </Reveal>
      </div>
      )}

      <p className="mt-5 font-mono text-[11px] leading-relaxed text-faint">
        {available
          ? "Auth-lite · no accounts. Your seat is saved to this browser so you can reconnect if the connection drops. Player data is the engine's real Cricsheet-derived catalog."
          : "Player data is the engine's real Cricsheet-derived catalog."}
      </p>
    </div>
  );
}
