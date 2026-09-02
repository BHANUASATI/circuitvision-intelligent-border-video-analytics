"""
ByteTrack — Multi-Object Tracker
Pure-Python implementation integrated inline.
Based on: https://arxiv.org/abs/2110.06864
Handles identity persistence across frames using IoU + Re-ID cost matrix.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import linear_sum_assignment


# ── Track State ──────────────────────────────────────────────

class TrackState(Enum):
    NEW = "new"
    TRACKED = "tracked"
    LOST = "lost"
    REMOVED = "removed"


@dataclass
class KalmanState:
    """Simple constant-velocity Kalman filter state for bbox tracking."""
    # State: [cx, cy, w, h, vx, vy, vw, vh]
    mean: np.ndarray = field(default_factory=lambda: np.zeros(8))
    covariance: np.ndarray = field(default_factory=lambda: np.eye(8) * 100)


@dataclass
class Track:
    track_id: int
    class_id: int
    label: str
    bbox: Tuple[int, int, int, int]          # x1, y1, x2, y2
    confidence: float
    state: TrackState = TrackState.NEW
    age: int = 1
    hit_streak: int = 1
    time_since_update: int = 0
    kalman: KalmanState = field(default_factory=KalmanState)

    @property
    def tlwh(self) -> np.ndarray:
        x1, y1, x2, y2 = self.bbox
        return np.array([x1, y1, x2 - x1, y2 - y1], dtype=float)

    @property
    def center(self) -> Tuple[float, float]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def predict(self) -> None:
        """Apply constant-velocity prediction."""
        F = np.eye(8)
        for i in range(4):
            F[i, i + 4] = 1.0
        self.kalman.mean = F @ self.kalman.mean
        self.time_since_update += 1

    def update(self, bbox: Tuple[int, int, int, int], conf: float) -> None:
        self.bbox = bbox
        self.confidence = conf
        self.time_since_update = 0
        self.hit_streak += 1
        self.age += 1
        self.state = TrackState.TRACKED


# ── IoU Helper ───────────────────────────────────────────────

def _iou_batch(boxes_a: np.ndarray, boxes_b: np.ndarray) -> np.ndarray:
    """
    Vectorised IoU between two sets of boxes [x1,y1,x2,y2].
    Returns matrix of shape (len(a), len(b)).
    """
    area_a = (boxes_a[:, 2] - boxes_a[:, 0]) * (boxes_a[:, 3] - boxes_a[:, 1])
    area_b = (boxes_b[:, 2] - boxes_b[:, 0]) * (boxes_b[:, 3] - boxes_b[:, 1])

    inter_x1 = np.maximum(boxes_a[:, None, 0], boxes_b[None, :, 0])
    inter_y1 = np.maximum(boxes_a[:, None, 1], boxes_b[None, :, 1])
    inter_x2 = np.minimum(boxes_a[:, None, 2], boxes_b[None, :, 2])
    inter_y2 = np.minimum(boxes_a[:, None, 3], boxes_b[None, :, 3])

    inter_w = np.maximum(0.0, inter_x2 - inter_x1)
    inter_h = np.maximum(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    union_area = area_a[:, None] + area_b[None, :] - inter_area
    return inter_area / (union_area + 1e-6)


# ── ByteTracker ───────────────────────────────────────────────

class ByteTracker:
    """
    Multi-class ByteTrack implementation.
    Maintains separate track pools for high-confidence and low-confidence detections.

    Usage:
        tracker = ByteTracker()
        tracks = tracker.update(detections, frame_id)
    """

    def __init__(
        self,
        high_thresh: float = 0.5,
        low_thresh: float = 0.1,
        match_thresh: float = 0.8,
        max_lost_frames: int = 30,
        min_hits: int = 3,
    ) -> None:
        self.high_thresh = high_thresh
        self.low_thresh = low_thresh
        self.match_thresh = match_thresh
        self.max_lost_frames = max_lost_frames
        self.min_hits = min_hits

        self._next_id = 1
        self.tracked_tracks: List[Track] = []
        self.lost_tracks: List[Track] = []
        self.removed_tracks: List[Track] = []

    # ── Main Update ───────────────────────────────────────────

    def update(self, detections: List[dict], frame_id: int) -> List[Track]:
        """
        detections: list of dicts with keys bbox, class_id, label, confidence
        Returns list of confirmed, active Track objects.
        """
        # Predict existing tracks
        for t in self.tracked_tracks + self.lost_tracks:
            t.predict()

        # Split detections by confidence
        high_dets = [d for d in detections if d["confidence"] >= self.high_thresh]
        low_dets  = [d for d in detections if self.low_thresh <= d["confidence"] < self.high_thresh]

        # ── Step 1: Match high-confidence dets to tracked tracks ──
        unmatched_tracks, unmatched_high = self._match_and_update(
            self.tracked_tracks, high_dets
        )

        # ── Step 2: Match low-confidence dets to unmatched tracks ──
        remaining_tracks = [self.tracked_tracks[i] for i in unmatched_tracks]
        unmatched_tracks2, _ = self._match_and_update(remaining_tracks, low_dets)

        # ── Step 3: Match unmatched high-dets to lost tracks ──────
        self._match_and_update(self.lost_tracks, [high_dets[i] for i in unmatched_high])

        # ── Step 4: Init new tracks from unmatched high-dets ──────
        for i in unmatched_high:
            d = high_dets[i]
            track = Track(
                track_id=self._next_id,
                class_id=d["class_id"],
                label=d["label"],
                bbox=tuple(d["bbox"]),
                confidence=d["confidence"],
            )
            self._next_id += 1
            self.tracked_tracks.append(track)

        # ── Lifecycle management ───────────────────────────────────
        lost_ids = {t.track_id for i in unmatched_tracks2
                    for t in [remaining_tracks[i]]}
        new_lost = []
        new_tracked = []
        for t in self.tracked_tracks:
            if t.track_id in lost_ids:
                t.state = TrackState.LOST
                new_lost.append(t)
            else:
                new_tracked.append(t)
        self.tracked_tracks = new_tracked

        # Age out lost tracks
        survived_lost = []
        for t in self.lost_tracks:
            if t.time_since_update <= self.max_lost_frames:
                survived_lost.append(t)
            else:
                t.state = TrackState.REMOVED
                self.removed_tracks.append(t)
        self.lost_tracks = survived_lost + new_lost

        # Return only confirmed tracks (hit_streak >= min_hits)
        return [t for t in self.tracked_tracks if t.hit_streak >= self.min_hits]

    # ── Matching ──────────────────────────────────────────────

    def _match_and_update(
        self,
        tracks: List[Track],
        dets: List[dict],
    ) -> Tuple[List[int], List[int]]:
        """
        Hungarian algorithm matching via IoU cost.
        Returns (unmatched_track_indices, unmatched_det_indices).
        """
        if not tracks or not dets:
            return list(range(len(tracks))), list(range(len(dets)))

        track_boxes = np.array([t.bbox for t in tracks], dtype=float)
        det_boxes   = np.array([d["bbox"] for d in dets], dtype=float)

        iou_matrix = _iou_batch(track_boxes, det_boxes)
        cost_matrix = 1.0 - iou_matrix

        row_idx, col_idx = linear_sum_assignment(cost_matrix)

        matched_tracks, matched_dets = set(), set()
        for r, c in zip(row_idx, col_idx):
            if iou_matrix[r, c] >= (1 - self.match_thresh):
                tracks[r].update(tuple(dets[c]["bbox"]), dets[c]["confidence"])
                matched_tracks.add(r)
                matched_dets.add(c)

        unmatched_tracks = [i for i in range(len(tracks)) if i not in matched_tracks]
        unmatched_dets   = [i for i in range(len(dets))   if i not in matched_dets]
        return unmatched_tracks, unmatched_dets

    def reset(self) -> None:
        self.tracked_tracks.clear()
        self.lost_tracks.clear()
        self.removed_tracks.clear()
        self._next_id = 1
