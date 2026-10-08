import { getToken } from "./auth";

export interface MaterialProgressEvent {
  type: "material_progress";
  payload: {
    material_id: string;
    stage: string;
    current: number;
    total: number;
    error_message: string | null;
  };
  ts: string;
}

export interface LevelCreatedEvent {
  type: "level_created";
  payload: { level_id: string; class_id: string; title: string; order_index: number };
  ts: string;
}

export interface LeaderboardUpdatedEvent {
  type: "leaderboard_updated";
  payload: { class_id: string };
  ts: string;
}

export interface LiveSessionUpdateEvent {
  type: "live_session_update";
  payload: Record<string, unknown>;
  ts: string;
}

export type RealtimeEvent =
  | MaterialProgressEvent
  | LevelCreatedEvent
  | LeaderboardUpdatedEvent
  | LiveSessionUpdateEvent;

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
const POLL_INTERVAL_MS = 4000;
const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 15000;

/**
 * Sambungkan ke channel WebSocket dengan fallback polling wajib jika
 * WebSocket gagal/terputus (lihat AGENTS.md bagian 9). `poll` dipanggil
 * secara berkala baik saat fallback maupun sebagai pengaman tambahan.
 */
export function connectRealtime(
  path: string,
  onEvent: (event: RealtimeEvent) => void,
  poll?: () => void
): () => void {
  let stopped = false;
  let socket: WebSocket | null = null;
  let reconnectDelay = RECONNECT_BASE_MS;
  let pollTimer: ReturnType<typeof setInterval> | null = null;

  function startPolling() {
    if (pollTimer || !poll) return;
    poll();
    pollTimer = setInterval(poll, POLL_INTERVAL_MS);
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function connect() {
    if (stopped) return;
    const token = getToken();
    const url = `${WS_URL}${path}${token ? `?token=${encodeURIComponent(token)}` : ""}`;
    try {
      socket = new WebSocket(url);
    } catch {
      startPolling();
      return;
    }

    socket.onopen = () => {
      reconnectDelay = RECONNECT_BASE_MS;
      stopPolling();
    };
    socket.onmessage = (event) => {
      try {
        onEvent(JSON.parse(event.data) as RealtimeEvent);
      } catch {
        // abaikan pesan yang tidak valid
      }
    };
    socket.onerror = () => {
      startPolling();
    };
    socket.onclose = () => {
      startPolling();
      if (stopped) return;
      setTimeout(connect, reconnectDelay);
      reconnectDelay = Math.min(reconnectDelay * 2, RECONNECT_MAX_MS);
    };
  }

  connect();

  return () => {
    stopped = true;
    stopPolling();
    socket?.close();
  };
}
