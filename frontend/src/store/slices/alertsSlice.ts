import { createAsyncThunk, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { alertsApi } from "@/api/endpoints";
import type { Alert, AlertFilter } from "@/types";

interface AlertsState {
  items: Alert[];
  counts: Record<string, number>;
  loading: boolean;
  liveAlerts: Alert[];   // incoming real-time alerts (capped at 100)
}

const initialState: AlertsState = {
  items: [], counts: {}, loading: false, liveAlerts: [],
};

export const fetchAlerts = createAsyncThunk(
  "alerts/fetch",
  async (filters: Partial<AlertFilter> = {}) => alertsApi.list(filters)
);

export const fetchCounts = createAsyncThunk("alerts/counts", async () => alertsApi.counts());

export const ackAlert = createAsyncThunk(
  "alerts/ack",
  async ({ id, status }: { id: string; status: string }) => {
    await alertsApi.acknowledge(id, status);
    return { id, status };
  }
);

const alertsSlice = createSlice({
  name: "alerts",
  initialState,
  reducers: {
    pushLiveAlert(state, { payload }: PayloadAction<Alert>) {
      state.liveAlerts.unshift(payload);
      if (state.liveAlerts.length > 100) state.liveAlerts.pop();
      // Also prepend to items list
      state.items.unshift(payload);
    },
    clearLive(state) { state.liveAlerts = []; },
  },
  extraReducers: (b) => {
    b.addCase(fetchAlerts.pending,   (s) => { s.loading = true; })
     .addCase(fetchAlerts.fulfilled, (s, { payload }) => { s.loading = false; s.items = payload; })
     .addCase(fetchAlerts.rejected,  (s) => { s.loading = false; })
     .addCase(fetchCounts.fulfilled, (s, { payload }) => { s.counts = payload; })
     .addCase(ackAlert.fulfilled,    (s, { payload }) => {
       const idx = s.items.findIndex((a) => a.alert_id === payload.id);
       if (idx >= 0) s.items[idx] = { ...s.items[idx], status: payload.status as Alert["status"] };
     });
  },
});

export const { pushLiveAlert, clearLive } = alertsSlice.actions;
export default alertsSlice.reducer;
