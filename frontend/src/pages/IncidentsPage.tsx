import { useEffect, useState } from "react";
import { Plus, AlertTriangle } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { incidentsApi } from "@/api/endpoints";
import { useAppDispatch } from "@/store/hooks";
import { addToast } from "@/store/slices/uiSlice";
import SeverityBadge from "@/components/common/SeverityBadge";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import type { Incident } from "@/types";
import { clsx } from "clsx";

const STATUS_COLOR: Record<string, string> = {
  open:       "text-red-400",
  resolved:   "text-green-400",
  in_progress:"text-amber-400",
};

export default function IncidentsPage() {
  const dispatch = useAppDispatch();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading,   setLoading]   = useState(true);
  const [showForm,  setShowForm]  = useState(false);
  const [form, setForm] = useState({ title: "", description: "", severity: "HIGH" });

  const load = async () => {
    setLoading(true);
    try { setIncidents(await incidentsApi.list()); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    try {
      await incidentsApi.create({ ...form, camera_id: undefined, alert_ids: [] });
      dispatch(addToast({ type: "success", message: "Incident created" }));
      setShowForm(false);
      load();
    } catch {
      dispatch(addToast({ type: "error", message: "Failed to create incident" }));
    }
  };

  const handleResolve = async (id: string) => {
    try {
      await incidentsApi.update(id, { status: "resolved" });
      dispatch(addToast({ type: "success", message: "Incident resolved" }));
      load();
    } catch {
      dispatch(addToast({ type: "error", message: "Failed to resolve" }));
    }
  };

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Incidents</h1>
          <p className="text-sm text-slate-500">{incidents.filter(i => i.status === "open").length} open</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowForm(true)}>
          <Plus size={15} /> New Incident
        </button>
      </div>

      {loading ? <LoadingSpinner /> : (
        <div className="space-y-3">
          {incidents.map((inc) => (
            <div key={inc.id} className="card flex items-start gap-4">
              <div className="flex-shrink-0 mt-0.5">
                <AlertTriangle size={16} className={STATUS_COLOR[inc.status] ?? "text-slate-500"} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-1">
                  <h3 className="font-semibold text-sm text-slate-200 truncate">{inc.title}</h3>
                  <SeverityBadge severity={inc.severity as never} />
                  <span className={clsx("text-xs font-medium", STATUS_COLOR[inc.status])}>
                    {inc.status.toUpperCase()}
                  </span>
                </div>
                {inc.description && (
                  <p className="text-xs text-slate-400 mb-2">{inc.description}</p>
                )}
                <p className="text-[10px] text-slate-600">
                  {formatDistanceToNow(new Date(inc.created_at), { addSuffix: true })}
                  {inc.camera_id && ` · ${inc.camera_id}`}
                </p>
              </div>
              {inc.status === "open" && (
                <button
                  onClick={() => handleResolve(inc.id)}
                  className="flex-shrink-0 text-xs text-green-400 hover:text-green-300 font-medium"
                >
                  Resolve
                </button>
              )}
            </div>
          ))}
          {incidents.length === 0 && (
            <div className="text-center py-12 text-slate-500 text-sm">No incidents recorded</div>
          )}
        </div>
      )}

      {/* Create form modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-40 p-4">
          <div className="card w-full max-w-md space-y-4">
            <h2 className="text-base font-bold text-slate-100">Create Incident</h2>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Title</label>
              <input className="input" value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })} />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Description</label>
              <textarea className="input" rows={3} value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Severity</label>
              <select className="input" value={form.severity}
                onChange={(e) => setForm({ ...form, severity: e.target.value })}>
                <option>CRITICAL</option><option>HIGH</option><option>MEDIUM</option><option>LOW</option>
              </select>
            </div>
            <div className="flex gap-2">
              <button className="btn-primary flex-1" onClick={handleCreate}>Create</button>
              <button className="btn-ghost flex-1" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
