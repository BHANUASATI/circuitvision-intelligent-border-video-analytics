/**
 * useWebSocket — connects to the backend alert WebSocket.
 * Dispatches incoming alerts into Redux store.
 */
import { useEffect, useRef } from "react";
import { useAppDispatch } from "@/store/hooks";
import { pushLiveAlert } from "@/store/slices/alertsSlice";
import { addToast } from "@/store/slices/uiSlice";
import type { WsMessage } from "@/types";

const WS_BASE = import.meta.env.VITE_WS_URL ?? `ws://${window.location.host}`;

export function useAlertWebSocket() {
  const dispatch   = useAppDispatch();
  const wsRef      = useRef<WebSocket | null>(null);
  const retryTimer = useRef<ReturnType<typeof setTimeout>>();
  const retries    = useRef(0);

  useEffect(() => {
    function connect() {
      const token = localStorage.getItem("access_token");
      if (!token) return;

      const url = `${WS_BASE}/api/v1/ws/alerts?token=${token}`;
      const ws  = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        retries.current = 0;
        dispatch(addToast({ type: "success", message: "Live alert stream connected" }));
      };

      ws.onmessage = (evt) => {
        try {
          const msg: WsMessage = JSON.parse(evt.data);
          if (msg.type === "alert" && msg.payload) {
            dispatch(pushLiveAlert(msg.payload));
            // Toast for HIGH/CRITICAL
            if (["HIGH", "CRITICAL"].includes(msg.payload.severity)) {
              dispatch(addToast({
                type: "warning",
                message: `${msg.payload.severity} — ${msg.payload.event_type.replace(/_/g, " ")} on ${msg.payload.camera_id}`,
              }));
            }
          } else if (msg.type === "ping") {
            ws.send(JSON.stringify({ action: "ping" }));
          }
        } catch { /* ignore malformed messages */ }
      };

      ws.onclose = () => {
        const delay = Math.min(1000 * 2 ** retries.current, 30_000);
        retries.current++;
        retryTimer.current = setTimeout(connect, delay);
      };

      ws.onerror = () => ws.close();
    }

    connect();
    return () => {
      clearTimeout(retryTimer.current);
      wsRef.current?.close();
    };
  }, [dispatch]);

  return wsRef;
}
