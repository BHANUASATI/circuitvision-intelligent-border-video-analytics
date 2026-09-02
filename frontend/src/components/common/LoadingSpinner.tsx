import { clsx } from "clsx";

export default function LoadingSpinner({ fullScreen = false }: { fullScreen?: boolean }) {
  return (
    <div className={clsx("flex items-center justify-center", fullScreen && "h-screen w-screen bg-surface")}>
      <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}
