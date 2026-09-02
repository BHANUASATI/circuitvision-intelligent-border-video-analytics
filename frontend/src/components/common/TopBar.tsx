import { Bell, PanelRightClose, LogOut, User } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { logout } from "@/store/slices/authSlice";
import { toggleAlertPanel } from "@/store/slices/uiSlice";
import { format } from "date-fns";

export default function TopBar() {
  const dispatch      = useAppDispatch();
  const navigate      = useNavigate();
  const user          = useAppSelector((s) => s.auth.user);
  const liveCount     = useAppSelector((s) => s.alerts.liveAlerts.length);
  const alertPanelOpen = useAppSelector((s) => s.ui.alertPanelOpen);

  const handleLogout = () => {
    dispatch(logout());
    navigate("/login");
  };

  return (
    <header className="flex items-center justify-between px-6 py-3 bg-surface-card border-b border-surface-border flex-shrink-0">
      <div>
        <p className="text-xs text-slate-500">{format(new Date(), "EEEE, dd MMM yyyy • HH:mm")}</p>
      </div>

      <div className="flex items-center gap-2">
        {/* Live alert badge */}
        <button
          onClick={() => dispatch(toggleAlertPanel())}
          className={`relative btn-ghost ${alertPanelOpen ? "text-brand-400" : ""}`}
          title="Toggle alert feed"
        >
          <Bell size={18} />
          {liveCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-severity-high text-white text-[9px] font-bold w-4 h-4 rounded-full flex items-center justify-center animate-pulse-alert">
              {liveCount > 99 ? "99" : liveCount}
            </span>
          )}
        </button>

        <button
          onClick={() => dispatch(toggleAlertPanel())}
          className={`btn-ghost ${alertPanelOpen ? "text-brand-400" : ""}`}
          title="Toggle side panel"
        >
          <PanelRightClose size={18} />
        </button>

        {/* User menu */}
        <div className="flex items-center gap-2 pl-2 border-l border-surface-border">
          <div className="w-7 h-7 rounded-full bg-brand-600 flex items-center justify-center">
            <User size={14} />
          </div>
          {user && <span className="text-sm text-slate-300 hidden sm:block">{user.username}</span>}
          <button onClick={handleLogout} className="btn-ghost text-slate-500" title="Logout">
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  );
}
