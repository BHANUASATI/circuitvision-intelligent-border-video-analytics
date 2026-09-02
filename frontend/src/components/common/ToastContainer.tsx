import { useEffect } from "react";
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from "lucide-react";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { removeToast } from "@/store/slices/uiSlice";
import { clsx } from "clsx";

const ICON = {
  success: <CheckCircle size={16} className="text-green-400" />,
  error:   <AlertCircle size={16} className="text-red-400" />,
  info:    <Info size={16} className="text-blue-400" />,
  warning: <AlertTriangle size={16} className="text-amber-400" />,
};

function Toast({ id, type, message }: { id: string; type: string; message: string }) {
  const dispatch = useAppDispatch();
  useEffect(() => {
    const t = setTimeout(() => dispatch(removeToast(id)), 4000);
    return () => clearTimeout(t);
  }, [id, dispatch]);

  return (
    <div className={clsx(
      "flex items-start gap-3 px-4 py-3 rounded-xl shadow-xl",
      "bg-surface-card border border-surface-border animate-slide-in",
      "w-72 max-w-full"
    )}>
      {ICON[type as keyof typeof ICON]}
      <p className="text-sm text-slate-200 flex-1">{message}</p>
      <button onClick={() => dispatch(removeToast(id))} className="text-slate-500 hover:text-slate-300">
        <X size={14} />
      </button>
    </div>
  );
}

export default function ToastContainer() {
  const toasts = useAppSelector((s) => s.ui.toasts);
  return (
    <div className="fixed bottom-4 right-4 flex flex-col gap-2 z-50">
      {toasts.map((t) => <Toast key={t.id} {...t} />)}
    </div>
  );
}
