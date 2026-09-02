"""
Virtual Fence — Intrusion Detection
Supports:
  • Line-crossing detection (uni/bi-directional)
  • Polygon zone intrusion detection
Uses Shapely for geometric calculations.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np
from shapely.geometry import LineString, Point, Polygon

from ai_service.utils.logger import logger


# ── Types ─────────────────────────────────────────────────────

class FenceType(str, Enum):
    LINE = "line"
    POLYGON = "polygon"


class CrossingDirection(str, Enum):
    ANY = "any"
    A_TO_B = "a_to_b"   # left-to-right or north-to-south
    B_TO_A = "b_to_a"


@dataclass
class FenceConfig:
    fence_id: str
    fence_type: FenceType
    name: str
    camera_id: str
    points: List[Tuple[int, int]]   # [[x,y], [x,y], ...]
    direction: CrossingDirection = CrossingDirection.ANY
    alert_cooldown: int = 30         # seconds between repeated alerts


@dataclass
class IntrusionEvent:
    fence_id: str
    fence_name: str
    track_id: int
    label: str
    bbox: Tuple[int, int, int, int]
    crossing_point: Optional[Tuple[float, float]]
    timestamp: float = field(default_factory=time.time)
    camera_id: str = ""


# ── Fence Registry ────────────────────────────────────────────

class VirtualFenceManager:
    """
    Manages multiple virtual fences per camera.
    Tracks object crossings and zone intrusions.
    """

    def __init__(self) -> None:
        self._fences: Dict[str, FenceConfig] = {}
        # track_id -> {fence_id -> last_position (side)}
        self._track_sides: Dict[int, Dict[str, int]] = {}
        # fence_id -> {track_id -> last_alert_time}
        self._alert_times: Dict[str, Dict[int, float]] = {}

    # ── Configuration ─────────────────────────────────────────

    def add_fence(self, config: FenceConfig) -> None:
        self._fences[config.fence_id] = config
        self._alert_times[config.fence_id] = {}
        logger.info(f"Virtual fence added: {config.fence_id} ({config.fence_type})")

    def remove_fence(self, fence_id: str) -> None:
        self._fences.pop(fence_id, None)
        self._alert_times.pop(fence_id, None)

    def get_fences_for_camera(self, camera_id: str) -> List[FenceConfig]:
        return [f for f in self._fences.values() if f.camera_id == camera_id]

    # ── Per-Frame Analysis ────────────────────────────────────

    def check_frame(
        self,
        camera_id: str,
        tracks: List[dict],   # {track_id, label, bbox}
    ) -> List[IntrusionEvent]:
        """
        Check all tracks against all fences for this camera.
        Returns list of intrusion events (deduplicated by cooldown).
        """
        events: List[IntrusionEvent] = []
        fences = self.get_fences_for_camera(camera_id)

        for fence in fences:
            for track in tracks:
                track_id = track["track_id"]
                bbox = track["bbox"]
                center = self._bbox_center(bbox)

                if fence.fence_type == FenceType.LINE:
                    event = self._check_line_crossing(fence, track_id, track["label"], bbox, center)
                else:
                    event = self._check_zone_intrusion(fence, track_id, track["label"], bbox, center)

                if event and self._should_alert(fence, track_id):
                    events.append(event)
                    self._alert_times[fence.fence_id][track_id] = time.time()

        return events

    # ── Line Crossing ─────────────────────────────────────────

    def _check_line_crossing(
        self,
        fence: FenceConfig,
        track_id: int,
        label: str,
        bbox: Tuple[int, int, int, int],
        center: Tuple[float, float],
    ) -> Optional[IntrusionEvent]:
        if len(fence.points) < 2:
            return None

        line = LineString(fence.points)
        side = self._point_side(center, fence.points[0], fence.points[1])

        prev_side = self._track_sides.get(track_id, {}).get(fence.fence_id)

        if prev_side is None:
            self._set_side(track_id, fence.fence_id, side)
            return None

        if prev_side != side and side != 0:
            # Crossing detected
            if fence.direction == CrossingDirection.ANY:
                crossed = True
            elif fence.direction == CrossingDirection.A_TO_B:
                crossed = prev_side == -1 and side == 1
            else:
                crossed = prev_side == 1 and side == -1

            self._set_side(track_id, fence.fence_id, side)

            if crossed:
                return IntrusionEvent(
                    fence_id=fence.fence_id,
                    fence_name=fence.name,
                    track_id=track_id,
                    label=label,
                    bbox=bbox,
                    crossing_point=center,
                    camera_id=fence.camera_id,
                )

        self._set_side(track_id, fence.fence_id, side)
        return None

    # ── Zone Intrusion ────────────────────────────────────────

    def _check_zone_intrusion(
        self,
        fence: FenceConfig,
        track_id: int,
        label: str,
        bbox: Tuple[int, int, int, int],
        center: Tuple[float, float],
    ) -> Optional[IntrusionEvent]:
        if len(fence.points) < 3:
            return None

        poly = Polygon(fence.points)
        pt = Point(center)

        if poly.contains(pt):
            return IntrusionEvent(
                fence_id=fence.fence_id,
                fence_name=fence.name,
                track_id=track_id,
                label=label,
                bbox=bbox,
                crossing_point=center,
                camera_id=fence.camera_id,
            )
        return None

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _bbox_center(bbox: Tuple[int, int, int, int]) -> Tuple[float, float]:
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    @staticmethod
    def _point_side(
        point: Tuple[float, float],
        line_start: Tuple[int, int],
        line_end: Tuple[int, int],
    ) -> int:
        """
        Returns +1 if point is on the left side of the directed line,
        -1 if on the right, 0 if on the line.
        """
        x, y = point
        x1, y1 = line_start
        x2, y2 = line_end
        val = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
        if val > 0:
            return 1
        elif val < 0:
            return -1
        return 0

    def _set_side(self, track_id: int, fence_id: str, side: int) -> None:
        if track_id not in self._track_sides:
            self._track_sides[track_id] = {}
        self._track_sides[track_id][fence_id] = side

    def _should_alert(self, fence: FenceConfig, track_id: int) -> bool:
        last = self._alert_times[fence.fence_id].get(track_id, 0)
        return (time.time() - last) > fence.alert_cooldown

    def cleanup_stale_tracks(self, active_track_ids: List[int]) -> None:
        """Remove track state for tracks no longer active."""
        stale = [tid for tid in self._track_sides if tid not in active_track_ids]
        for tid in stale:
            del self._track_sides[tid]


# Singleton
fence_manager = VirtualFenceManager()
