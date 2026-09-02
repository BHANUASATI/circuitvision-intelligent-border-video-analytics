import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Camera, Bell, AlertTriangle,
  BarChart3, Users, Shield, ChevronLeft,
} from "lucide-react";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { toggleSidebar } from "@/store/slices/uiSlice";
import { clsx } from "clsx";

const NAV = [
  { to: "/dashboard",  icon: LayoutDashboard, label: "Dashboard"  },
  { to: "/cameras",    icon: Camera,           label: "Cameras"    },
  { to: "/alerts",     icon: Bell,             label: "Alerts"     },
  { to: "/incidents",  icon: AlertTriangle,    label: "Incidents"  },
  { to: "/analytics",  icon: BarChart3,        label: "Analytics"  },
  { to: "/users",      icon: Users,            label: "Users"      },
];

export default function Sidebar() {
  const open     = useAppSelector((s) => s.ui.sidebarOpen);
  const counts   = useAppSelector((s) => s.alerts.counts);
  const dispatch = useAppDispatch();
  const unread   = counts["HIGH"] ?? 0 + (counts["CRITICAL"] ?? 0);

  return (
    <aside
      className={clsx(
        "flex flex-col bg-surface-card border-r border-surface-border transition-all duration-200 flex-shrink-0",
        open ? "w-56" : "w-14"
      )}
    >
      {/* Brand */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-surface-border">
        {open && (
          <div>
            <div className="flex items-center gap-2">
              <Shield className="text-brand-500" size={20} />
              <span className="font-bold text-sm tracking-wide text-slate-100">IBVAP</span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">Border Intelligence</p>
          </div>
        )}
        <button onClick={() => dispatch(toggleSidebar())} className="btn-ghost p-1.5 rounded-lg">
          <ChevronLeft size={16} className={clsx("transition-transform", !open && "rotate-180")} />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 space-y-0.5 px-2">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-brand-600/20 text-brand-400"
                  : "text-slate-400 hover:text-slate-100 hover:bg-surface"
              )
            }
          >
            <div className="relative flex-shrink-0">
              <Icon size={18} />
              {to === "/alerts" && unread > 0 && (
                <span className="absolute -top-1.5 -right-1.5 bg-severity-high text-white text-[9px] font-bold w-3.5 h-3.5 rounded-full flex items-center justify-center">
                  {unread > 9 ? "9+" : unread}
                </span>
              )}
            </div>
            {open && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Status dot */}
      {open && (
        <div className="px-4 py-3 border-t border-surface-border">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            System Operational
          </div>
        </div>
      )}
    </aside>
  );
}
