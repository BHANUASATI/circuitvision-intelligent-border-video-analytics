import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { authApi } from "@/api/endpoints";
import type { LoginRequest, User } from "@/types";

interface AuthState {
  token: string | null;
  user: User | null;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  token:   localStorage.getItem("access_token"),
  user:    null,
  loading: false,
  error:   null,
};

export const login = createAsyncThunk(
  "auth/login",
  async (credentials: LoginRequest, { rejectWithValue }) => {
    try {
      const tokens = await authApi.login(credentials);
      localStorage.setItem("access_token",  tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      const user = await authApi.me();
      return { tokens, user };
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? "Login failed";
      return rejectWithValue(msg);
    }
  }
);

export const verifyAuth = createAsyncThunk("auth/verify", async (_, { rejectWithValue }) => {
  const token = localStorage.getItem("access_token");
  if (!token) return rejectWithValue("No token");
  try {
    return await authApi.me();
  } catch {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    return rejectWithValue("Session expired");
  }
});

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    logout(state) {
      state.token = null;
      state.user  = null;
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    },
    clearError(state) { state.error = null; },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending,  (s) => { s.loading = true; s.error = null; })
      .addCase(login.fulfilled, (s, { payload }) => {
        s.loading = false;
        s.token   = payload.tokens.access_token;
        s.user    = payload.user;
      })
      .addCase(login.rejected, (s, { payload }) => {
        s.loading = false;
        s.error   = payload as string;
      })
      .addCase(verifyAuth.pending,    (s) => { s.loading = true; })
      .addCase(verifyAuth.fulfilled,  (s, { payload }) => { s.loading = false; s.user = payload; })
      .addCase(verifyAuth.rejected,   (s) => { s.loading = false; s.token = null; s.user = null; });
  },
});

export const { logout, clearError } = authSlice.actions;
export default authSlice.reducer;
