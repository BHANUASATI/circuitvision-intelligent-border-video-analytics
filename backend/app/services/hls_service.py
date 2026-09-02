"""
HLS Service — RTSP → HLS transcoding via FFmpeg.

Each camera gets its own FFmpeg subprocess that writes HLS segments
to a temp directory. Stderr is captured so callers can surface the
real FFmpeg error to the user instead of a generic timeout message.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Dict, Optional

from app.core.logger import logger

# ── State ─────────────────────────────────────────────────────

class _HLSSession:
    def __init__(self, camera_id: str, proc: subprocess.Popen, hls_dir: Path):
        self.camera_id  = camera_id
        self.proc       = proc
        self.hls_dir    = hls_dir
        self.stderr_buf: list[str] = []
        # Drain stderr in a background thread so the pipe never blocks
        self._stderr_thread = threading.Thread(
            target=self._drain_stderr, daemon=True
        )
        self._stderr_thread.start()

    def _drain_stderr(self) -> None:
        assert self.proc.stderr is not None
        for raw in self.proc.stderr:
            line = raw.decode(errors="replace").rstrip()
            if line:
                self.stderr_buf.append(line)
                logger.debug(f"[ffmpeg/{self.camera_id}] {line}")

    def last_error(self) -> str:
        """Return the last few meaningful stderr lines."""
        relevant = [l for l in self.stderr_buf if any(
            kw in l.lower() for kw in ("error", "failed", "invalid", "refused",
                                        "timeout", "no such", "connection", "unauthorized")
        )]
        lines = relevant[-3:] if relevant else self.stderr_buf[-3:]
        return " | ".join(lines) if lines else "No output from FFmpeg"


_sessions: Dict[str, _HLSSession] = {}

FFMPEG_PATH = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"


def _hls_dir_for(camera_id: str) -> Path:
    base = Path(tempfile.gettempdir()) / "ibvap_hls"
    d = base / camera_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _build_ffmpeg_cmd(stream_url: str, hls_dir: Path, transport: str = "tcp") -> list[str]:
    """Build the FFmpeg command for RTSP → HLS transcoding."""
    playlist = hls_dir / "index.m3u8"
    cmd = [
        FFMPEG_PATH,
        "-loglevel",        "warning",
        "-timeout",         "10000000",      # RTSP/HTTP timeout in µs (10 s)
        "-rtsp_transport",  transport,
        "-i",               stream_url,
        "-c:v",             "libx264",
        "-preset",          "ultrafast",
        "-tune",            "zerolatency",
        "-crf",             "28",
        "-an",                               # drop audio — faster startup
        "-f",               "hls",
        "-hls_time",        "2",
        "-hls_list_size",   "5",
        "-hls_flags",       "delete_segments+append_list",
        "-hls_segment_filename", str(hls_dir / "seg%03d.ts"),
        str(playlist),
    ]
    return cmd


def start_hls(camera_id: str, stream_url: str) -> Path:
    """
    Launch FFmpeg to transcode stream_url → HLS.
    Returns the HLS directory. Idempotent if already running.
    Raises RuntimeError with a descriptive message on failure.
    """
    # Reuse existing healthy session
    if camera_id in _sessions:
        sess = _sessions[camera_id]
        if sess.proc.poll() is None:
            logger.debug(f"HLS session already active for {camera_id}")
            return sess.hls_dir
        logger.warning(f"HLS process for {camera_id} died — restarting")
        _cleanup_session(camera_id)

    hls_dir = _hls_dir_for(camera_id)

    # Clean stale segments
    for f in hls_dir.glob("*.ts"):
        f.unlink(missing_ok=True)
    (hls_dir / "index.m3u8").unlink(missing_ok=True)

    cmd = _build_ffmpeg_cmd(stream_url, hls_dir, transport="tcp")
    logger.info(f"Starting HLS transcode [{camera_id}]: {stream_url}")

    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    sess = _HLSSession(camera_id, proc, hls_dir)
    _sessions[camera_id] = sess
    return hls_dir


def stop_hls(camera_id: str) -> None:
    _cleanup_session(camera_id)


def get_hls_dir(camera_id: str) -> Optional[Path]:
    sess = _sessions.get(camera_id)
    if sess:
        return sess.hls_dir
    d = _hls_dir_for(camera_id)
    if (d / "index.m3u8").exists():
        return d
    return None


def get_last_error(camera_id: str) -> str:
    sess = _sessions.get(camera_id)
    return sess.last_error() if sess else "No active session"


def is_running(camera_id: str) -> bool:
    sess = _sessions.get(camera_id)
    return bool(sess and sess.proc.poll() is None)


def _cleanup_session(camera_id: str) -> None:
    sess = _sessions.pop(camera_id, None)
    if not sess:
        return
    try:
        sess.proc.terminate()
        sess.proc.wait(timeout=3)
    except Exception:
        try:
            sess.proc.kill()
        except Exception:
            pass
    shutil.rmtree(sess.hls_dir, ignore_errors=True)
    logger.info(f"HLS session cleaned up for {camera_id}")
