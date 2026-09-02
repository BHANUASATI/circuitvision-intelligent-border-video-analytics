/**
 * Real-time alert feed sidebar — shows live alerts from WebSocket.
 */
import { formatDistanceToNow } from "date-fns";
import {
  ShieldAlert, Car, Eye, UserSearch,
  Activity, Moon, Flame, Trash2,
} from "lucide-react";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { ackAlert, clearLive } from "@/store/slices/alertsSlice";
import SeverityBadge from "@/components/common/SeverityBadge";
import type { Alert, EventType } from "@/types";

const EVENT_ICON: Record<EventType, React.ReactNode> = {
  intrusion:        <ShieldAlert size={14} className="text-red-400" />,
  face_alert:       <UserSearch  size={14} className="text-purple-400" />,
  anpr:             <Car         size={14} className="text-blue-400" />,
  loitering:        <Eye         size={14} className="text-amber-400" />,
  crowding:         <Flame       size={14} className="text-orange-400" />,
  night_movement:   <Moon        size={14} className="text-indigo-400" />,
  running:          <Activity    size={14} className="text-yellow-400" />,
  erratic_movement: <Activity    size={14} className="text-pink-400" />,
  abandoned_object: <Trash2      size={14} className="text-slate-400" />,
};

function AlertCard({ alert }: { alert: Alert }) {
  const dispatch = useAppDispatch();

  return (
    <div className="border-b border-surface-border px-3 py-3 hover:bg-surface/50 transition-colors animate-fade-in">
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <div className="flex items-center gap-1.5 min-w-0">
          {EVENT_ICON[alert.event_type] ?? <ShieldAlert size={14} />}
          <span className="text-xs font-medium text-slate-200 truncate">
            {alert.event_type.replace(/_/g, " ").toUpperCase()}
          </span>
        </div>
        <SeverityBadge severity={alert.severity} />
      </div>

      <p className="text-xs text-slate-400 mb-1 truncate">{alert.description}</p>

      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono text-slate-500">{alert.camera_id}</span>
        <span className="text-[10px] text-slate-600">
          {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
        </span>
      </div>

      {alert.status === "new" && (
        <button
          onClick={() => dispatch(ackAlert({ id: alert.alert_id, status: "acknowledged" }))}
          className="mt-2 w-full text-[10px] text-brand-400 hover:text-brand-300 font-medium transition-colors"
        >
          Acknowledge
        </button>
      )}
    </div>
  );
}

export default function AlertFeed() {
  const dispatch   = useAppDispatch();
  const liveAlerts = useAppSelector((s) => s.alerts.liveAlerts);

  return (
    <div className="h-full flex flex-col bg-surface-card">
      <div className="flex items-center justify-between px-3 py-3 border-b border-surface-border flex-shrink-0">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse-alert" />
          <h3 className="text-sm font-semibold text-slate-200">Live Alerts</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge bg-surface text-slate-400 border border-surface-border">
            {liveAlerts.length}
          </span>
          {liveAlerts.length > 0 && (
            <button
              onClick={() => dispatch(clearLive())}
              className="text-[10px] text-slate-500 hover:text-slate-300"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {liveAlerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-slate-600 gap-2">
            <ShieldAlert size={24} />
            <p className="text-xs">No live alerts</p>
          </div>
        ) : (
          liveAlerts.map((alert) => <AlertCard key={alert.alert_id} alert={alert} />)
        )}
      </div>
    </div>
  );
}
