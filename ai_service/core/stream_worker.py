"""
Stream Worker — per-camera async task
Ingests RTSP/ONVIF stream via OpenCV/PyAV and runs the full AI pipeline:
  YOLO detection → ByteTrack → Face Rec → ANPR → Intrusion → Activity → Alert
"""
from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

import cv2
import numpy as np

from ai_service.configs.settings import settings
from ai_service.modules.activity.activity_detector import ActivityDetector
from ai_service.modules.anpr.anpr import anpr_engine
from ai_service.modules.detection.detector import detector
from ai_service.modules.face_recognition.face_engine import face_engine
from ai_service.modules.intrusion.virtual_fence import fence_manager
from ai_service.modules.tracking.bytetrack import ByteTracker
from ai_service.utils.evidence import evidence_manager
from ai_service.utils.logger import logger
from ai_service.utils.redis_client import publish_alert, set_stream_state


# ── Camera Config ─────────────────────────────────────────────

class StreamStatus(str, Enum):
    CONNECTING = "connecting"
    RUNNING = "running"
    RECONNECTING = "reconnecting"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class CameraConfig:
    camera_id: str
    name: str
    stream_url: str               # rtsp://... or http://...
    location: str = ""
    enable_detection: bool = True
    enable_face_recognition: bool = True
    enable_anpr: bool = True
    enable_intrusion: bool = True
    enable_activity: bool = True
    frame_skip: int = settings.stream_frame_skip
    fps_target: float = 25.0


@dataclass
class StreamStats:
    camera_id: str
    status: StreamStatus = StreamStatus.CONNECTING
    fps: float = 0.0
    frame_count: int = 0
    inference_ms: float = 0.0
    alert_count: int = 0
    last_frame_ts: float = field(default_factory=time.time)
    error: Optional[str] = None


# ── Stream Worker ─────────────────────────────────────────────

class StreamWorker:
    """
    One worker per camera. Runs in an asyncio task.
    Uses run_in_executor to keep CV/AI work off the event loop.
    """

    def __init__(self, config: CameraConfig) -> None:
        self.config = config
        self.stats = StreamStats(camera_id=config.camera_id)

        # Per-worker module instances
        self._tracker = ByteTracker(
            high_thresh=settings.yolo_confidence_threshold,
            low_thresh=0.1,
        )
        self._activity = ActivityDetector()

        self._stop_event = asyncio.Event()
        self._cap: Optional[cv2.VideoCapture] = None

    # ── Lifecycle ─────────────────────────────────────────────

    async def start(self) -> None:
        logger.info(f"[{self.config.camera_id}] Stream worker starting: {self.config.stream_url}")
        self.stats.status = StreamStatus.CONNECTING
        await self._run_loop()

    async def stop(self) -> None:
        self._stop_event.set()
        if self._cap:
            self._cap.release()
        self.stats.status = StreamStatus.STOPPED
        logger.info(f"[{self.config.camera_id}] Stream worker stopped")

    # ── Main Loop ─────────────────────────────────────────────

    async def _run_loop(self) -> None:
        loop = asyncio.get_event_loop()
        reconnect_delay = settings.stream_reconnect_delay

        while not self._stop_event.is_set():
            try:
                # Open capture in thread pool
                cap = await loop.run_in_executor(
                    None, self._open_capture, self.config.stream_url
                )
                if cap is None or not cap.isOpened():
                    raise ConnectionError("Failed to open stream")

                self._cap = cap
                self.stats.status = StreamStatus.RUNNING
                self.stats.error = None
                logger.success(f"[{self.config.camera_id}] Stream connected")
                await set_stream_state(self.config.camera_id, {"status": "running"})

                frame_id = 0
                fps_counter = 0
                fps_timer = time.time()

                while not self._stop_event.is_set():
                    # Read frame in executor (blocking IO)
                    ret, frame = await loop.run_in_executor(None, cap.read)
                    if not ret or frame is None:
                        logger.warning(f"[{self.config.camera_id}] Frame read failed — reconnecting")
                        break

                    frame_id += 1
                    fps_counter += 1
                    self.stats.frame_count += 1
                    self.stats.last_frame_ts = time.time()

                    # FPS calc every 30 frames
                    if fps_counter >= 30:
                        elapsed = time.time() - fps_timer
                        self.stats.fps = round(fps_counter / elapsed, 1)
                        fps_counter = 0
                        fps_timer = time.time()

                    # Skip frames to reduce load
                    if frame_id % self.config.frame_skip != 0:
                        continue

                    # Run AI pipeline in thread pool
                    await loop.run_in_executor(
                        None, self._process_frame, frame, frame_id
                    )

            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.stats.status = StreamStatus.RECONNECTING
                self.stats.error = str(exc)
                logger.error(f"[{self.config.camera_id}] Stream error: {exc}")
                await set_stream_state(
                    self.config.camera_id,
                    {"status": "reconnecting", "error": str(exc)},
                )
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, 60)   # exponential backoff

            finally:
                if self._cap:
                    self._cap.release()
                    self._cap = None

    # ── AI Pipeline ───────────────────────────────────────────

    def _process_frame(self, frame: np.ndarray, frame_id: int) -> None:
        """
        Full synchronous AI pipeline executed in a thread pool worker.
        """
        cfg = self.config
        cam_id = cfg.camera_id
        t0 = time.perf_counter()
        alerts = []

        # 1. Object detection
        det_result = detector.detect(frame, cam_id, frame_id)
        raw_dets = [
            {
                "bbox": list(d.bbox),
                "class_id": d.class_id,
                "label": d.label,
                "confidence": d.confidence,
            }
            for d in det_result.detections
        ]

        # 2. Multi-object tracking
        active_tracks = self._tracker.update(raw_dets, frame_id)
        track_dicts = [
            {
                "track_id": t.track_id,
                "label": t.label,
                "class_id": t.class_id,
                "bbox": list(t.bbox),
                "confidence": t.confidence,
            }
            for t in active_tracks
        ]

        # 3. Virtual fence / intrusion detection
        if cfg.enable_intrusion:
            intrusion_events = fence_manager.check_frame(cam_id, track_dicts)
            for evt in intrusion_events:
                alert = self._build_alert("intrusion", cam_id, {
                    "fence_id": evt.fence_id,
                    "fence_name": evt.fence_name,
                    "track_id": evt.track_id,
                    "label": evt.label,
                    "bbox": list(evt.bbox),
                    "crossing_point": evt.crossing_point,
                })
                alerts.append(alert)
                evidence_manager.save_frame(frame, cam_id, "intrusion", alert)

        # 4. Suspicious activity detection
        if cfg.enable_activity:
            activity_alerts = self._activity.analyse(cam_id, track_dicts, frame)
            for act in activity_alerts:
                alert = self._build_alert(act.activity_type.value, cam_id, {
                    "description": act.description,
                    "severity": act.severity,
                    "track_ids": act.track_ids,
                })
                alerts.append(alert)

        # 5. Face recognition (sampled — every 5th processed frame)
        if cfg.enable_face_recognition and frame_id % 5 == 0:
            face_matches = face_engine.detect_and_recognize(frame, cam_id)
            for match in face_matches:
                if match.is_watchlisted or match.is_unknown:
                    alert = self._build_alert("face_alert", cam_id, {
                        "identity_id": match.identity_id,
                        "identity_name": match.identity_name,
                        "similarity": round(match.similarity, 3),
                        "is_unknown": match.is_unknown,
                        "is_watchlisted": match.is_watchlisted,
                        "bbox": list(match.face.bbox),
                    })
                    alerts.append(alert)
                    evidence_manager.save_frame(frame, cam_id, "face_alert", alert)

        # 6. ANPR (vehicles only, sampled every 3rd frame)
        if cfg.enable_anpr and frame_id % 3 == 0:
            vehicle_tracks = [t for t in track_dicts if t["label"] in ("car", "motorcycle", "bus", "truck")]
            if vehicle_tracks:
                plate_results = anpr_engine.process_frame(frame, cam_id)
                for pr in plate_results:
                    alert = self._build_alert("anpr", cam_id, {
                        "plate_text": pr.plate_text,
                        "confidence": round(pr.confidence, 3),
                        "is_watchlisted": pr.is_watchlisted,
                        "watchlist_entry": pr.watchlist_entry,
                        "bbox": list(pr.bbox),
                    })
                    if pr.is_watchlisted:
                        alerts.append(alert)
                        evidence_manager.save_frame(frame, cam_id, "anpr_watchlist", alert)

        # 7. Publish alerts via Redis
        for alert in alerts:
            asyncio.run_coroutine_threadsafe(
                publish_alert("ibvap:alerts", alert),
                asyncio.get_event_loop(),
            )
            self.stats.alert_count += 1

        self.stats.inference_ms = round((time.perf_counter() - t0) * 1000, 2)

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _open_capture(url: str) -> cv2.VideoCapture:
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        return cap

    @staticmethod
    def _build_alert(event_type: str, camera_id: str, data: Dict[str, Any]) -> dict:
        return {
            "alert_id": str(uuid.uuid4()),
            "event_type": event_type,
            "camera_id": camera_id,
            "timestamp": time.time(),
            "data": data,
        }
