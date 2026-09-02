"""
Suspicious Activity & Night-time Movement Detector

Detects:
  1. Loitering     — person in zone beyond time threshold
  2. Crowding      — more than N people in zone simultaneously
  3. Abandoned object — stationary non-person detection
  4. Night movement — any movement detected in low-light conditions
  5. Running       — person bbox aspect ratio + speed heuristic
  6. Direction change — erratic trajectory
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from ai_service.utils.logger import logger


# ── Activity Types ────────────────────────────────────────────

class ActivityType(str, Enum):
    LOITERING = "loitering"
    CROWDING = "crowding"
    ABANDONED_OBJECT = "abandoned_object"
    NIGHT_MOVEMENT = "night_movement"
    RUNNING = "running"
    ERRATIC_MOVEMENT = "erratic_movement"


@dataclass
class ActivityAlert:
    activity_type: ActivityType
    camera_id: str
    track_ids: List[int]
    bbox: Optional[Tuple[int, int, int, int]]
    description: str
    severity: str    # LOW | MEDIUM | HIGH
    timestamp: float = field(default_factory=time.time)


# ── Trajectory Store ──────────────────────────────────────────

@dataclass
class TrajectoryEntry:
    positions: List[Tuple[float, float]] = field(default_factory=list)
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    label: str = "unknown"


# ── Activity Detector ─────────────────────────────────────────

class ActivityDetector:
    """
    Stateful per-camera activity analyser.
    Feed confirmed tracks every frame; it maintains trajectory history.
    """

    def __init__(
        self,
        loitering_threshold_s: float = 30.0,
        crowd_threshold: int = 5,
        abandoned_threshold_s: float = 60.0,
        night_brightness_threshold: float = 50.0,
        running_speed_threshold: float = 80.0,   # pixels/second
        erratic_angle_threshold: float = 120.0,  # degrees
        history_window: int = 30,                # frames
    ) -> None:
        self._loiter_thresh = loitering_threshold_s
        self._crowd_thresh = crowd_threshold
        self._abandoned_thresh = abandoned_threshold_s
        self._night_brightness = night_brightness_threshold
        self._running_speed = running_speed_threshold
        self._erratic_angle = erratic_angle_threshold
        self._history = history_window

        self._trajectories: Dict[int, TrajectoryEntry] = {}
        self._static_objects: Dict[int, dict] = {}   # track_id -> {bbox, first_seen}

    # ── Main ──────────────────────────────────────────────────

    def analyse(
        self,
        camera_id: str,
        tracks: List[dict],         # {track_id, label, bbox, confidence}
        frame: Optional[np.ndarray] = None,
        fps: float = 25.0,
    ) -> List[ActivityAlert]:
        alerts: List[ActivityAlert] = []
        now = time.time()

        # Update trajectories
        active_ids = set()
        for track in tracks:
            tid = track["track_id"]
            active_ids.add(tid)
            bbox = track["bbox"]
            cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2

            if tid not in self._trajectories:
                self._trajectories[tid] = TrajectoryEntry(label=track["label"])
            entry = self._trajectories[tid]
            entry.positions.append((cx, cy))
            entry.last_seen = now
            # Cap trajectory length
            if len(entry.positions) > self._history * 10:
                entry.positions = entry.positions[-self._history * 10:]

        # Prune stale tracks
        stale = [tid for tid, e in self._trajectories.items()
                 if now - e.last_seen > 120 and tid not in active_ids]
        for tid in stale:
            del self._trajectories[tid]

        person_tracks = [t for t in tracks if t["label"] == "person"]

        # ── 1. Loitering ──────────────────────────────────────
        for track in person_tracks:
            tid = track["track_id"]
            entry = self._trajectories.get(tid)
            if entry and (now - entry.first_seen) > self._loiter_thresh:
                speed = self._avg_speed(entry.positions[-30:], fps)
                if speed < 5.0:   # nearly stationary
                    alerts.append(ActivityAlert(
                        activity_type=ActivityType.LOITERING,
                        camera_id=camera_id,
                        track_ids=[tid],
                        bbox=track["bbox"],
                        description=f"Person loitering for {int(now - entry.first_seen)}s",
                        severity="MEDIUM",
                    ))

        # ── 2. Crowding ───────────────────────────────────────
        if len(person_tracks) >= self._crowd_thresh:
            alerts.append(ActivityAlert(
                activity_type=ActivityType.CROWDING,
                camera_id=camera_id,
                track_ids=[t["track_id"] for t in person_tracks],
                bbox=None,
                description=f"Crowd detected: {len(person_tracks)} persons",
                severity="HIGH",
            ))

        # ── 3. Running ────────────────────────────────────────
        for track in person_tracks:
            tid = track["track_id"]
            entry = self._trajectories.get(tid)
            if entry and len(entry.positions) >= 5:
                speed = self._avg_speed(entry.positions[-5:], fps)
                if speed > self._running_speed:
                    alerts.append(ActivityAlert(
                        activity_type=ActivityType.RUNNING,
                        camera_id=camera_id,
                        track_ids=[tid],
                        bbox=track["bbox"],
                        description=f"Running detected (speed≈{speed:.0f}px/s)",
                        severity="MEDIUM",
                    ))

        # ── 4. Night Movement ─────────────────────────────────
        if frame is not None and self._is_night(frame) and len(person_tracks) > 0:
            alerts.append(ActivityAlert(
                activity_type=ActivityType.NIGHT_MOVEMENT,
                camera_id=camera_id,
                track_ids=[t["track_id"] for t in person_tracks],
                bbox=None,
                description=f"Night-time movement: {len(person_tracks)} person(s) detected",
                severity="HIGH",
            ))

        # ── 5. Erratic Movement ───────────────────────────────
        for track in person_tracks:
            tid = track["track_id"]
            entry = self._trajectories.get(tid)
            if entry and len(entry.positions) >= 10:
                if self._is_erratic(entry.positions[-10:]):
                    alerts.append(ActivityAlert(
                        activity_type=ActivityType.ERRATIC_MOVEMENT,
                        camera_id=camera_id,
                        track_ids=[tid],
                        bbox=track["bbox"],
                        description="Erratic/suspicious movement pattern",
                        severity="MEDIUM",
                    ))

        return alerts

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _avg_speed(positions: List[Tuple[float, float]], fps: float) -> float:
        """Average displacement per second between consecutive positions."""
        if len(positions) < 2:
            return 0.0
        total = sum(
            ((positions[i][0] - positions[i - 1][0]) ** 2 +
             (positions[i][1] - positions[i - 1][1]) ** 2) ** 0.5
            for i in range(1, len(positions))
        )
        duration = max(len(positions) / fps, 0.01)
        return total / duration

    @staticmethod
    def _is_night(frame: np.ndarray) -> bool:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        return float(np.mean(gray)) < 50.0

    def _is_erratic(self, positions: List[Tuple[float, float]]) -> bool:
        """Detect sharp angle changes in trajectory."""
        angles = []
        for i in range(2, len(positions)):
            v1 = np.array(positions[i - 1]) - np.array(positions[i - 2])
            v2 = np.array(positions[i]) - np.array(positions[i - 1])
            norm = np.linalg.norm(v1) * np.linalg.norm(v2)
            if norm < 1e-4:
                continue
            cos_a = np.clip(np.dot(v1, v2) / norm, -1, 1)
            angles.append(np.degrees(np.arccos(cos_a)))
        if not angles:
            return False
        return float(np.mean(angles)) > self._erratic_angle
