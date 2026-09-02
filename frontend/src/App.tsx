import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { verifyAuth } from "@/store/slices/authSlice";
import Layout from "@/components/common/Layout";
import LoginPage from "@/pages/LoginPage";
import DashboardPage from "@/pages/DashboardPage";
import CamerasPage from "@/pages/CamerasPage";
import AlertsPage from "@/pages/AlertsPage";
import IncidentsPage from "@/pages/IncidentsPage";
import AnalyticsPage from "@/pages/AnalyticsPage";
import UsersPage from "@/pages/UsersPage";
import LoadingSpinner from "@/components/common/LoadingSpinner";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { token, loading } = useAppSelector((s) => s.auth);
  if (loading) return <LoadingSpinner fullScreen />;
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(verifyAuth());
  }, [dispatch]);

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard"  element={<DashboardPage />} />
        <Route path="cameras"    element={<CamerasPage />} />
        <Route path="alerts"     element={<AlertsPage />} />
        <Route path="incidents"  element={<IncidentsPage />} />
        <Route path="analytics"  element={<AnalyticsPage />} />
        <Route path="users"      element={<UsersPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
