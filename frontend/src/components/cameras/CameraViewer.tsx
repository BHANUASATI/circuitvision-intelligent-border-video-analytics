/**
 * CameraViewer — full-screen modal HLS player.
 *
 * Flow:
 *  1. Mount → POST /api/v1/stream/{camera_id}/start  (backend spawns FFmpeg)
 *  2. Backend waits for first segment, returns playlist_url
 *  3. hls.js attaches to <video> and plays the HLS stream
 *  4. Unmount → POST /api/v1/stream/{camera_id}/stop  (kills FFmpeg)
 */
import { useEffect, useRef, useState, useCallback } from "react";
import Hls from "hls.js";
import { X, Loader2, AlertTriangle, Maximize2, Minimize2, Volume2, VolumeX } from "lucide-react";
import { apiClient } from "@/api/client";
import type { Camera } from "@/types";

interface Props {
  camera: Camera;
  onClose: () => void;
}

type Phase = "starting" | "playing" | "error";

export default function CameraViewer({ camera, onClose }: Props) {
  const videoRef    = useRef<HTMLVideoElement>(null);
  const hlsRef      = useRef<Hls | null>(null);
  const [phase, setPhase]         = useState<Phase>("starting");
  const [errMsg, setErrMsg]       = useState("");
  const [fullscreen, setFullscreen] = useState(false);
  const [muted, setMuted]         = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);

  // ── Start stream ────────────────────────────────────────────
  useEffect(() => {
    let destroyed = false;

    const startAndPlay = async () => {
      try {
        // Ask backend to start FFmpeg → HLS
        const res = await apiClient.post<{ playlist_url: string }>(
          `/stream/${camera.camera_id}/start`
        );
        if (destroyed) return;

        const playlistUrl = res.data.playlist_url;   // e.g. /api/v1/stream/cam1/hls/index.m3u8

        const video = videoRef.current;
        if (!video) return;

        // Native HLS (Safari / iOS)
        if (!Hls.isSupported() && video.canPlayType("application/vnd.apple.mpegurl")) {
          video.src = playlistUrl;
          video.play().catch(() => {});
          setPhase("playing");
          return;
        }

        if (!Hls.isSupported()) {
          setErrMsg("HLS is not supported in this browser.");
          setPhase("error");
          return;
        }

        const hls = new Hls({
          lowLatencyMode: true,
          liveSyncDurationCount: 2,
          liveMaxLatencyDurationCount: 5,
          maxBufferLength: 10,
          backBufferLength: 0,
        });

        hlsRef.current = hls;
        hls.loadSource(playlistUrl);
        hls.attachMedia(video);

        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          if (!destroyed) {
            video.play().catch(() => {});
            setPhase("playing");
          }
        });

        hls.on(Hls.Events.ERROR, (_evt, data) => {
          if (data.fatal) {
            if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
              hls.startLoad();          // try to recover network errors
            } else {
              setErrMsg(`Stream error: ${data.details}`);
              setPhase("error");
            }
          }
        });
      } catch (err: unknown) {
        if (!destroyed) {
          const detail =
            (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
            ?? "Failed to start stream. Check the stream URL is reachable.";
          // Split "FFmpeg said: …" onto its own line for readability
          const [main, ...rest] = detail.split("FFmpeg said:");
          setErrMsg(
            rest.length
              ? `${main.trim()}\n\nFFmpeg: ${rest.join("").trim()}`
              : main.trim()
          );
          setPhase("error");
        }
      }
    };

    startAndPlay();

    return () => {
      destroyed = true;
      hlsRef.current?.destroy();
      hlsRef.current = null;
      // Stop FFmpeg process on backend
      apiClient.post(`/stream/${camera.camera_id}/stop`).catch(() => {});
    };
  }, [camera.camera_id]);

  // ── Fullscreen toggle ────────────────────────────────────────
  const toggleFullscreen = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    if (!document.fullscreenElement) {
      el.requestFullscreen().then(() => setFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setFullscreen(false)).catch(() => {});
    }
  }, []);

  useEffect(() => {
    const handler = () => setFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, []);

  // ── Close on Escape ──────────────────────────────────────────
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
      <div
        ref={containerRef}
        className="relative w-full max-w-5xl bg-black rounded-xl overflow-hidden shadow-2xl border border-surface-border"
      >
        {/* ── Top bar ── */}
        <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-4 py-2.5 bg-gradient-to-b from-black/80 to-transparent">
          <div className="flex items-center gap-2">
            {/* Live dot */}
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
            </span>
            <span className="text-xs font-semibold text-white tracking-wide">
              {camera.name}
            </span>
            <span className="text-[10px] font-mono text-slate-400">{camera.camera_id}</span>
            {camera.location && (
              <span className="text-[10px] text-slate-500">· {camera.location}</span>
            )}
          </div>

          <div className="flex items-center gap-1">
            {/* Mute toggle */}
            <button
              onClick={() => {
                if (videoRef.current) videoRef.current.muted = !muted;
                setMuted((m) => !m);
              }}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
            >
              {muted ? <VolumeX size={15} /> : <Volume2 size={15} />}
            </button>
            {/* Fullscreen */}
            <button
              onClick={toggleFullscreen}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
            >
              {fullscreen ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
            </button>
            {/* Close */}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
            >
              <X size={15} />
            </button>
          </div>
        </div>

        {/* ── Video ── */}
        <div className="relative bg-black" style={{ aspectRatio: "16/9" }}>
          <video
            ref={videoRef}
            className="w-full h-full object-contain"
            muted={muted}
            playsInline
            autoPlay
          />

          {/* Starting overlay */}
          {phase === "starting" && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/70">
              <Loader2 size={32} className="text-brand-400 animate-spin" />
              <p className="text-sm text-slate-300">Connecting to stream…</p>
              <p className="text-[11px] text-slate-500 font-mono truncate max-w-xs px-4 text-center">
                {camera.stream_url}
              </p>
            </div>
          )}

          {/* Error overlay */}
          {phase === "error" && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/80 px-6 text-center">
              <AlertTriangle size={32} className="text-red-400" />
              <p className="text-sm font-semibold text-slate-200">Stream Unavailable</p>
              <p className="text-xs text-slate-400 max-w-sm whitespace-pre-wrap">{errMsg}</p>
              <p className="text-[10px] font-mono text-slate-600 truncate max-w-xs">
                {camera.stream_url}
              </p>
              <button
                className="mt-2 btn-primary text-xs px-4 py-1.5"
                onClick={() => { setPhase("starting"); setErrMsg(""); }}
              >
                Retry
              </button>
            </div>
          )}
        </div>

        {/* ── Bottom info bar ── */}
        <div className="flex items-center gap-4 px-4 py-2 bg-black/60 text-[10px] text-slate-500 font-mono border-t border-white/5">
          <span>RTSP → HLS</span>
          <span className="truncate flex-1">{camera.stream_url}</span>
          <span
            className={
              phase === "playing" ? "text-green-400" :
              phase === "error"   ? "text-red-400" : "text-amber-400"
            }
          >
            {phase.toUpperCase()}
          </span>
        </div>
      </div>
    </div>
  );
}
