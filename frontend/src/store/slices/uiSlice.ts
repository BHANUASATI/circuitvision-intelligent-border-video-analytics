import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface Toast { id: string; type: "success" | "error" | "info" | "warning"; message: string; }

interface UiState {
  sidebarOpen: boolean;
  toasts: Toast[];
  alertPanelOpen: boolean;
}

const initialState: UiState = { sidebarOpen: true, toasts: [], alertPanelOpen: true };

const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    toggleSidebar(s)   { s.sidebarOpen = !s.sidebarOpen; },
    toggleAlertPanel(s){ s.alertPanelOpen = !s.alertPanelOpen; },
    addToast(s, { payload }: PayloadAction<Omit<Toast, "id">>) {
      s.toasts.push({ ...payload, id: Date.now().toString() });
    },
    removeToast(s, { payload }: PayloadAction<string>) {
      s.toasts = s.toasts.filter((t) => t.id !== payload);
    },
  },
});

export const { toggleSidebar, toggleAlertPanel, addToast, removeToast } = uiSlice.actions;
export default uiSlice.reducer;
