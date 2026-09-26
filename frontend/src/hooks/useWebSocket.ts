import { useEffect, useRef } from "react";
import { useQueryClient, type QueryClient } from "@tanstack/react-query";
import type { BoardEvent } from "../types/api";

const WS_BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/^http/, "ws");

/**
 * Opens a WebSocket to /ws/boards/{boardId} and keeps the "cards" query
 * cache in sync with live events from other connected clients.
 *
 * Cookies (including access_token) are sent automatically on the WS
 * handshake by the browser — no manual auth header needed, same as your
 * regular fetch/axios requests.
 */
export function useBoardWebSocket(boardId: string | undefined) {
  const queryClient = useQueryClient();
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!boardId) return;

    const socket = new WebSocket(`${WS_BASE}/ws/boards/${boardId}`);
    socketRef.current = socket;

    socket.onmessage = (event: MessageEvent<string>) => {
      const message = JSON.parse(event.data) as BoardEvent;
      handleEvent(queryClient, boardId, message);
    };

    socket.onclose = (event: CloseEvent) => {
      if (event.code === 4401) {
        console.warn(
          "WebSocket auth failed — access token may have expired without a prior REST call to refresh it."
        );
      }
    };

    return () => {
      socket.close();
    };
  }, [boardId, queryClient]);

  return socketRef;
}

function handleEvent(queryClient: QueryClient, boardId: string, message: BoardEvent): void {
  switch (message.type) {
    case "card_created":
    case "card_updated":
    case "card_moved":
    case "card_deleted":
      // Simplest correct approach: just refetch this board's lists/cards.
      // A more advanced version would surgically patch the cache using
      // payload.card_id / payload.list_id — worth doing later if refetch
      // traffic becomes a real concern, not needed for a portfolio project.
      queryClient.invalidateQueries({ queryKey: ["boards", boardId, "lists"] });
      break;
    default:
      break;
  }
}
