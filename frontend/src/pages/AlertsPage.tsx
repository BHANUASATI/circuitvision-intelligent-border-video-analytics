import { useEffect, useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { Filter, RefreshCw, CheckCheck } from "lucide-react";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { ackAlert, fetchAlerts } from "@/store/slices/alertsSlice";
import { addToast } from "@/store/slices/uiSlice";
import SeverityBadge from "@/components/common/SeverityBadge";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import { clsx } from "clsx";
import type { AlertStatus } from "@/types";

const STATUS_COLORS: Record<AlertStatus, string> = {
  new:           "status-new",
  acknowledged:  "status-acknowledged",
  resolved:      "status-resolved",
  false_positive: "status-acknowledged",
};

export default function AlertsPage() {
  const dispatch = useAppDispatch();
  const { items, loading } = useAppSelector((s) => s.alerts);
  const cameras  = useAppSelector((s) => s.cameras.items);

  const [filterSeverity, setFilterSeverity] = useState("");
  const [filterStatus,   setFilterStatus]   = useState("new");
  const [filterCamera,   setFilterCamera]   = useState("");

  const load = () => {
    dispatch(fetchAlerts({
      severity:  filterSeverity  || undefined,
      status:    filterStatus    || undefined,
      camera_id: filterCamera    || undefined,
      page_size: 100,
    }));
  };

  useEffect(load, [filterSeverity, filterStatus, filterCamera]);

  const handleAck = async (alertId: string, status: string) => {
    try {
      await dispatch(ackAlert({ id: alertId, status })).unwrap();
      dispatch(addToast({ type: "success", message: "Alert updated" }));
    } catch {
      dispatch(addToast({ type: "error", message: "Failed to update alert" }));
    }
  };

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Alerts</h1>
          <p className="text-sm text-slate-500">{items.length} alerts displayed</p>
        </div>
        <button onClick={load} className="btn-ghost flex items-center gap-2 text-sm">
          <RefreshCw size={15} className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="card flex flex-wrap gap-3 items-center">
        <Filter size={14} className="text-slate-500" />

        <select className="input w-auto text-xs" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="new">New</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="resolved">Resolved</option>
          <option value="false_positive">False Positive</option>
        </select>

        <select className="input w-auto text-xs" value={filterSeverity} onChange={(e) => setFilterSeverity(e.target.value)}>
          <option value="">All severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>

        <select className="input w-auto text-xs" value={filterCamera} onChange={(e) => setFilterCamera(e.target.value)}>
          <option value="">All cameras</option>
          {cameras.map((c) => <option key={c.camera_id} value={c.camera_id}>{c.name}</option>)}
        </select>
      </div>

      {/* Table */}
      {loading ? <LoadingSpinner /> : (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-border">
                  {["Time","Camera","Event Type","Severity","Status","Description","Actions"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-medium text-slate-500 whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.map((alert) => (
                  <tr key={alert.id} className="border-b border-surface-border hover:bg-surface/50 transition-colors">
                    <td className="px-4 py-3 text-xs font-mono text-slate-500 whitespace-nowrap">
                      {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-slate-300 whitespace-nowrap">
                      {alert.camera_id}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="text-xs font-medium text-slate-300">
                        {alert.event_type.replace(/_/g, " ").toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <SeverityBadge severity={alert.severity} />
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={clsx("badge text-[10px]", STATUS_COLORS[alert.status])}>
                        {alert.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400 max-w-xs truncate">
                      {alert.description}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {alert.status === "new" && (
                        <div className="flex gap-1">
                          <button
                            onClick={() => handleAck(alert.alert_id, "acknowledged")}
                            className="text-[10px] text-brand-400 hover:text-brand-300 font-medium"
                          >
                            ACK
                          </button>
                          <span className="text-slate-700">·</span>
                          <button
                            onClick={() => handleAck(alert.alert_id, "false_positive")}
                            className="text-[10px] text-slate-500 hover:text-slate-300 font-medium"
                          >
                            FP
                          </button>
                        </div>
                      )}
                      {alert.status === "acknowledged" && (
                        <button
                          onClick={() => handleAck(alert.alert_id, "resolved")}
                          className="text-[10px] text-green-400 hover:text-green-300 font-medium flex items-center gap-0.5"
                        >
                          <CheckCheck size={10} /> Resolve
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-slate-500 text-sm">
                      No alerts found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
