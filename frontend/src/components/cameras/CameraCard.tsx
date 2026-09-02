import { Play, Square, Wifi, WifiOff, MapPin, Settings, Eye } from "lucide-react";
import { useAppDispatch } from "@/store/hooks";
import { startStream, stopStream } from "@/store/slices/camerasSlice";
import { addToast } from "@/store/slices/uiSlice";
import type { Camera } from "@/types";
import { clsx } from "clsx";

interface Props {
  camera: Camera;
  onEdit?: (c: Camera) => void;
  onView?: (c: Camera) => void;
}

export default function CameraCard({ camera, onEdit, onView }: Props) {
  const dispatch = useAppDispatch();

  const handleToggle = async () => {
    try {
      if (camera.is_streaming) {
        await dispatch(stopStream(camera.camera_id)).unwrap();
        dispatch(addToast({ type: "info", message: `Stream stopped: ${camera.name}` }));
      } else {
        await dispatch(startStream(camera.camera_id)).unwrap();
        dispatch(addToast({ type: "success", message: `Stream started: ${camera.name}` }));
      }
    } catch (err) {
      const msg = typeof err === "string" ? err : (err as { message?: string })?.message ?? "Failed to toggle stream";
      dispatch(addToast({ type: "error", message: msg }));
    }
  };

  return (
    <div className={clsx(
      "card flex flex-col gap-3 border transition-colors",
      camera.is_streaming ? "border-brand-600/40" : "border-surface-border"
    )}>
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="font-semibold text-sm text-slate-200 truncate">{camera.name}</h3>
          <p className="text-[10px] font-mono text-slate-500 mt-0.5">{camera.camera_id}</p>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          {camera.is_streaming
            ? <Wifi size={14} className="text-green-400" />
            : <WifiOff size={14} className="text-slate-600" />
          }
          <span className={clsx(
            "badge text-[10px]",
            camera.is_streaming ? "status-new" : "status-acknowledged"
          )}>
            {camera.is_streaming ? "LIVE" : "IDLE"}
          </span>
        </div>
      </div>

      {/* Location */}
      {camera.location && (
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <MapPin size={12} />
          <span className="truncate">{camera.location}</span>
        </div>
      )}

      {/* Feature pills */}
      <div className="flex flex-wrap gap-1">
        {[
          { key: "enable_detection",        label: "Detect" },
          { key: "enable_face_recognition", label: "Face" },
          { key: "enable_anpr",             label: "ANPR" },
          { key: "enable_intrusion",        label: "Fence" },
          { key: "enable_activity",         label: "Activity" },
        ].map(({ key, label }) => (
          <span
            key={key}
            className={clsx(
              "text-[9px] px-1.5 py-0.5 rounded-full border font-medium",
              camera[key as keyof Camera]
                ? "bg-brand-600/20 border-brand-600/40 text-brand-400"
                : "bg-surface border-surface-border text-slate-600"
            )}
          >
            {label}
          </span>
        ))}
      </div>

      {/* Stream URL */}
      <p className="text-[10px] font-mono text-slate-600 truncate">{camera.stream_url}</p>

      {/* Actions */}
      <div className="flex gap-2 pt-1 border-t border-surface-border">
        <button
          onClick={handleToggle}
          className={clsx(
            "flex items-center gap-1.5 flex-1 justify-center px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
            camera.is_streaming
              ? "bg-red-900/40 text-red-400 hover:bg-red-900/60 border border-red-800/50"
              : "btn-primary"
          )}
        >
          {camera.is_streaming
            ? <><Square size={12} /> Stop</>
            : <><Play  size={12} /> Start</>
          }
        </button>
        {onView && (
          <button
            onClick={() => onView(camera)}
            className="flex items-center gap-1 btn-ghost px-2 text-xs border border-surface-border rounded-lg hover:border-brand-600/40"
            title="View live feed"
          >
            <Eye size={13} />
          </button>
        )}
        {onEdit && (
          <button onClick={() => onEdit(camera)} className="btn-ghost px-2" title="Edit camera">
            <Settings size={14} />
          </button>
        )}
      </div>
    </div>
  );
}
