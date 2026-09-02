import { apiClient } from "./client";
import type {
  Alert, AlertFilter, Camera, CameraCreate, DashboardSummary,
  Incident, IncidentCreate, LoginRequest, TokenResponse, User, UserCreate,
} from "@/types";

// ── Auth ──────────────────────────────────────────────────────
export const authApi = {
  login: (data: LoginRequest) =>
    apiClient.post<TokenResponse>("/auth/login", data).then((r) => r.data),
  me: () => apiClient.get<User>("/auth/me").then((r) => r.data),
  refresh: (refresh_token: string) =>
    apiClient.post<TokenResponse>("/auth/refresh", { refresh_token }).then((r) => r.data),
  changePassword: (data: { current_password: string; new_password: string }) =>
    apiClient.post("/auth/change-password", data).then((r) => r.data),
};

// ── Cameras ───────────────────────────────────────────────────
export const camerasApi = {
  list: () => apiClient.get<Camera[]>("/cameras").then((r) => r.data),
  get: (id: string) => apiClient.get<Camera>(`/cameras/${id}`).then((r) => r.data),
  create: (data: CameraCreate) => apiClient.post<Camera>("/cameras", data).then((r) => r.data),
  update: (id: string, data: Partial<CameraCreate>) =>
    apiClient.patch<Camera>(`/cameras/${id}`, data).then((r) => r.data),
  remove: (id: string) => apiClient.delete(`/cameras/${id}`).then((r) => r.data),
  startStream: (id: string) => apiClient.post(`/cameras/${id}/start-stream`).then((r) => r.data),
  stopStream: (id: string) => apiClient.post(`/cameras/${id}/stop-stream`).then((r) => r.data),
  stats: (id: string) => apiClient.get(`/cameras/${id}/stats`).then((r) => r.data),
};

// ── Alerts ────────────────────────────────────────────────────
export const alertsApi = {
  list: (filters: Partial<AlertFilter> = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => v != null && params.append(k, String(v)));
    return apiClient.get<Alert[]>(`/alerts?${params}`).then((r) => r.data);
  },
  counts: () => apiClient.get<Record<string, number>>("/alerts/counts").then((r) => r.data),
  acknowledge: (id: string, status: string, note?: string) =>
    apiClient.patch(`/alerts/${id}/acknowledge`, { status, note }).then((r) => r.data),
};

// ── Incidents ─────────────────────────────────────────────────
export const incidentsApi = {
  list: () => apiClient.get<Incident[]>("/incidents").then((r) => r.data),
  create: (data: IncidentCreate) =>
    apiClient.post<Incident>("/incidents", data).then((r) => r.data),
  update: (id: string, data: Partial<IncidentCreate>) =>
    apiClient.patch<Incident>(`/incidents/${id}`, data).then((r) => r.data),
};

// ── Analytics ─────────────────────────────────────────────────
export const analyticsApi = {
  dashboard: () => apiClient.get<DashboardSummary>("/analytics/dashboard").then((r) => r.data),
  timeline: (cameraId?: string, hours = 24) =>
    apiClient.get("/analytics/alerts/timeline", {
      params: { camera_id: cameraId, hours },
    }).then((r) => r.data),
  heatmap: (hours = 24) =>
    apiClient.get("/analytics/cameras/heatmap", { params: { hours } }).then((r) => r.data),
};

// ── Users ─────────────────────────────────────────────────────
export const usersApi = {
  list: () => apiClient.get<User[]>("/users").then((r) => r.data),
  create: (data: UserCreate) => apiClient.post<User>("/users", data).then((r) => r.data),
  update: (id: string, data: Partial<User>) =>
    apiClient.patch<User>(`/users/${id}`, data).then((r) => r.data),
  remove: (id: string) => apiClient.delete(`/users/${id}`).then((r) => r.data),
};
