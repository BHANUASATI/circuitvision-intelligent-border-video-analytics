// ── Auth ──────────────────────────────────────────────────────
export interface LoginRequest { username: string; password: string; }
export interface TokenResponse {
  access_token: string; refresh_token: string;
  token_type: string; expires_in: number;
}
export interface User {
  id: string; username: string; email: string;
  full_name: string; is_active: boolean; is_superuser: boolean;
  role_id: string | null; last_login: string | null; created_at: string;
}
export interface UserCreate {
  username: string; email: string; full_name: string;
  password: string; role_id?: string;
}

// ── Camera ────────────────────────────────────────────────────
export interface Camera {
  id: string; camera_id: string; name: string;
  stream_url: string; location: string;
  latitude: number | null; longitude: number | null;
  enable_detection: boolean; enable_face_recognition: boolean;
  enable_anpr: boolean; enable_intrusion: boolean; enable_activity: boolean;
  frame_skip: number; is_active: boolean; is_streaming: boolean;
  created_at: string;
}
export interface CameraCreate {
  camera_id: string; name: string; stream_url: string;
  location: string; latitude?: number; longitude?: number;
  enable_detection?: boolean; enable_face_recognition?: boolean;
  enable_anpr?: boolean; enable_intrusion?: boolean; enable_activity?: boolean;
  frame_skip?: number;
}
export interface StreamStats {
  camera_id: string; status: string; fps: number;
  frame_count: number; inference_ms: number;
  alert_count: number; error: string | null;
}

// ── Alert ─────────────────────────────────────────────────────
export type AlertSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type AlertStatus   = "new" | "acknowledged" | "resolved" | "false_positive";
export type EventType =
  | "intrusion" | "face_alert" | "anpr" | "loitering"
  | "crowding" | "night_movement" | "running" | "erratic_movement" | "abandoned_object";

export interface Alert {
  id: string; alert_id: string; camera_id: string;
  event_type: EventType; severity: AlertSeverity; status: AlertStatus;
  description: string; payload: Record<string, unknown>;
  evidence_path: string | null; evidence_hash: string | null;
  created_at: string;
}
export interface AlertFilter {
  camera_id?: string; event_type?: string; severity?: string;
  status?: string; from_ts?: string; to_ts?: string;
  page?: number; page_size?: number;
}

// ── Incident ──────────────────────────────────────────────────
export interface Incident {
  id: string; title: string; description: string;
  severity: AlertSeverity; status: string;
  camera_id: string | null; assigned_to: string | null;
  created_at: string; resolved_at: string | null;
}
export interface IncidentCreate {
  title: string; description: string; severity: string;
  camera_id?: string; alert_ids?: string[];
}

// ── Analytics ─────────────────────────────────────────────────
export interface DashboardSummary {
  cameras: { total: number; active_streams: number; };
  alerts: {
    last_24h: number; unacknowledged: number;
    by_event_type: Record<string, number>;
    by_severity: Record<string, number>;
    hourly_trend: Array<{ hour: string; count: number }>;
  };
  incidents: { open: number; };
  generated_at: string;
}

// ── WebSocket ─────────────────────────────────────────────────
export interface WsMessage {
  type: "alert" | "connected" | "ping" | "pong" | "subscribed";
  payload?: Alert;
  camera_id?: string;
  message?: string;
}
