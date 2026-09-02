import { configureStore } from "@reduxjs/toolkit";
import authReducer    from "./slices/authSlice";
import alertsReducer  from "./slices/alertsSlice";
import camerasReducer from "./slices/camerasSlice";
import uiReducer      from "./slices/uiSlice";

export const store = configureStore({
  reducer: {
    auth:    authReducer,
    alerts:  alertsReducer,
    cameras: camerasReducer,
    ui:      uiReducer,
  },
  middleware: (getDefault) => getDefault({ serializableCheck: false }),
});

export type RootState    = ReturnType<typeof store.getState>;
export type AppDispatch  = typeof store.dispatch;
