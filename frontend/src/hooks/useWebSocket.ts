import { useCallback, useEffect, useRef, useState } from "react";
import type { WsMessage } from "@/types/websocket";
import { POLLING_INTERVALS } from "@/utils/constants";

export function useWebSocket(campaignId: number | null) {
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isUnmountedRef = useRef(false);

  const connect = useCallback(() => {
    if (!campaignId || isUnmountedRef.current) return;

    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${proto}//${window.location.host}/api/ws/campaigns/${campaignId}`;
    const ws = new WebSocket(url);

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => {
      setIsConnected(false);
      if (!isUnmountedRef.current) {
        reconnectTimerRef.current = setTimeout(connect, POLLING_INTERVALS.WS_RECONNECT);
      }
    };
    ws.onmessage = (event) => {
      try {
        setLastMessage(JSON.parse(event.data) as WsMessage);
      } catch {
        /* ignore non-JSON payloads */
      }
    };

    wsRef.current = ws;
  }, [campaignId]);

  useEffect(() => {
    isUnmountedRef.current = false;
    connect();
    return () => {
      isUnmountedRef.current = true;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [connect]);

  return { lastMessage, isConnected };
}
