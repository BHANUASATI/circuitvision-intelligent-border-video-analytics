import { createAsyncThunk, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { camerasApi } from "@/api/endpoints";
import type { Camera, StreamStats } from "@/types";

interface CamerasState {
  items: Camera[];
  stats: Record<string, StreamStats>;
  loading: boolean;
}

const initialState: CamerasState = { items: [], stats: {}, loading: false };

export const fetchCameras = createAsyncThunk("cameras/fetch", () => camerasApi.list());

export const startStream = createAsyncThunk(
  "cameras/start",
  async (id: string, { rejectWithValue }) => {
    try {
      await camerasApi.startStream(id);
      return id;
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Failed to start stream";
      return rejectWithValue(msg);
    }
  }
);

export const stopStream = createAsyncThunk(
  "cameras/stop",
  async (id: string, { rejectWithValue }) => {
    try {
      await camerasApi.stopStream(id);
      return id;
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Failed to stop stream";
      return rejectWithValue(msg);
    }
  }
);

const camerasSlice = createSlice({
  name: "cameras",
  initialState,
  reducers: {
    updateStats(state, { payload }: PayloadAction<StreamStats>) {
      state.stats[payload.camera_id] = payload;
    },
  },
  extraReducers: (b) => {
    b.addCase(fetchCameras.pending,   (s) => { s.loading = true; })
     .addCase(fetchCameras.fulfilled, (s, { payload }) => { s.loading = false; s.items = payload; })
     .addCase(fetchCameras.rejected,  (s) => { s.loading = false; })
     .addCase(startStream.fulfilled,  (s, { payload: id }) => {
       const c = s.items.find((x) => x.camera_id === id);
       if (c) c.is_streaming = true;
     })
     .addCase(stopStream.fulfilled,   (s, { payload: id }) => {
       const c = s.items.find((x) => x.camera_id === id);
       if (c) c.is_streaming = false;
     });
  },
});

export const { updateStats } = camerasSlice.actions;
export default camerasSlice.reducer;
