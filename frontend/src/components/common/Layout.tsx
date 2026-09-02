import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import ToastContainer from "./ToastContainer";
import AlertFeed from "../alerts/AlertFeed";
import { useAlertWebSocket } from "@/hooks/useWebSocket";
import { useAppSelector } from "@/store/hooks";

export default function Layout() {
  useAlertWebSocket();  // establish WS connection at layout level
  const alertPanelOpen = useAppSelector((s) => s.ui.alertPanelOpen);

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <TopBar />
        <div className="flex flex-1 overflow-hidden">
          <main className="flex-1 overflow-y-auto p-6">
            <Outlet />
          </main>
          {alertPanelOpen && (
            <aside className="w-80 border-l border-surface-border overflow-y-auto flex-shrink-0">
              <AlertFeed />
            </aside>
          )}
        </div>
      </div>
      <ToastContainer />
    </div>
  );
}
