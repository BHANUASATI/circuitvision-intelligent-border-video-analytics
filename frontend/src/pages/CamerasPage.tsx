import { useEffect, useState } from "react";
import { Plus, Search } from "lucide-react";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { fetchCameras } from "@/store/slices/camerasSlice";
import { addToast } from "@/store/slices/uiSlice";
import { camerasApi } from "@/api/endpoints";
import CameraCard from "@/components/cameras/CameraCard";
import CameraViewer from "@/components/cameras/CameraViewer";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import type { Camera, CameraCreate } from "@/types";

const EMPTY: CameraCreate = {
  camera_id: "", name: "", stream_url: "", location: "",
  enable_detection: true, enable_face_recognition: true,
  enable_anpr: true, enable_intrusion: true, enable_activity: true,
  frame_skip: 2,
};

function CameraForm({
  initial, onSave, onCancel,
}: {
  initial: CameraCreate;
  onSave: (d: CameraCreate) => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState(initial);
  const set = (k: string, v: unknown) => setForm((f) => ({ ...f, [k]: v }));

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-40 p-4">
      <div className="card w-full max-w-lg space-y-4">
        <h2 className="text-base font-bold text-slate-100">Add Camera</h2>

        <div className="grid grid-cols-2 gap-3">
          {[
            { k: "camera_id", label: "Camera ID", placeholder: "cam-bop-01" },
            { k: "name",      label: "Name",      placeholder: "BOP Gate A" },
          ].map(({ k, label, placeholder }) => (
            <div key={k}>
              <label className="block text-xs text-slate-400 mb-1">{label}</label>
              <input className="input" placeholder={placeholder}
                value={String(form[k as keyof CameraCreate] ?? "")}
                onChange={(e) => set(k, e.target.value)} />
            </div>
          ))}
        </div>

        <div>
          <label className="block text-xs text-slate-400 mb-1">Stream URL (RTSP/HTTP)</label>
          <input className="input" placeholder="rtsp://192.168.1.10:554/stream1"
            value={form.stream_url} onChange={(e) => set("stream_url", e.target.value)} />
        </div>

        <div>
          <label className="block text-xs text-slate-400 mb-1">Location</label>
          <input className="input" placeholder="BOP North Gate, Sector 7"
            value={form.location} onChange={(e) => set("location", e.target.value)} />
        </div>

        <div className="grid grid-cols-2 gap-2">
          {(["enable_detection","enable_face_recognition","enable_anpr","enable_intrusion","enable_activity"] as const).map((k) => (
            <label key={k} className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" className="rounded"
                checked={!!form[k]}
                onChange={(e) => set(k, e.target.checked)} />
              <span className="text-xs text-slate-400">{k.replace("enable_", "").replace(/_/g, " ")}</span>
            </label>
          ))}
        </div>

        <div className="flex gap-2 pt-2">
          <button className="btn-primary flex-1" onClick={() => onSave(form)}>Save Camera</button>
          <button className="btn-ghost flex-1" onClick={onCancel}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

export default function CamerasPage() {
  const dispatch = useAppDispatch();
  const { items: cameras, loading } = useAppSelector((s) => s.cameras);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [viewingCamera, setViewingCamera] = useState<Camera | null>(null);

  useEffect(() => { dispatch(fetchCameras()); }, [dispatch]);

  const filtered = cameras.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.camera_id.toLowerCase().includes(search.toLowerCase()) ||
      c.location.toLowerCase().includes(search.toLowerCase())
  );

  const handleAdd = async (data: CameraCreate) => {
    try {
      await camerasApi.create(data);
      dispatch(fetchCameras());
      setShowForm(false);
      dispatch(addToast({ type: "success", message: `Camera added: ${data.name}` }));
    } catch (err) {
      dispatch(addToast({ type: "error", message: `Failed to add camera: ${String(err)}` }));
    }
  };

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Cameras</h1>
          <p className="text-sm text-slate-500">{cameras.length} registered · {cameras.filter(c => c.is_streaming).length} streaming</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowForm(true)}>
          <Plus size={15} /> Add Camera
        </button>
      </div>

      <div className="relative">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
        <input
          className="input pl-9"
          placeholder="Search cameras..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filtered.map((c) => (
            <CameraCard key={c.id} camera={c} onView={setViewingCamera} />
          ))}
          {filtered.length === 0 && (
            <div className="col-span-full text-center py-12 text-slate-500 text-sm">
              No cameras found
            </div>
          )}
        </div>
      )}

      {showForm && (
        <CameraForm initial={EMPTY} onSave={handleAdd} onCancel={() => setShowForm(false)} />
      )}

      {viewingCamera && (
        <CameraViewer camera={viewingCamera} onClose={() => setViewingCamera(null)} />
      )}
    </div>
  );
}
