"""
YOLO-based multi-class detector.
Handles: person, vehicle types, motorcycle, bus, truck, car, bicycle.
Uses YOLOv8 via ultralytics — supports CUDA GPU acceleration.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from ai_service.configs.settings import settings
from ai_service.utils.logger import logger

# COCO class indices we care about
PERSON_CLASS = 0
VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
BICYCLE_CLASS = 1

# Merged mapping: class_id -> label
TRACKED_CLASSES: dict[int, str] = {
    PERSON_CLASS: "person",
    BICYCLE_CLASS: "bicycle",
    **VEHICLE_CLASSES,
}


@dataclass
class Detection:
    """Single detection result from YOLO."""
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    class_id: int
    label: str
    confidence: float
    frame_id: int = 0


@dataclass
class DetectionResult:
    """Full result for one frame."""
    frame_id: int
    camera_id: str
    detections: List[Detection] = field(default_factory=list)
    inference_ms: float = 0.0


class YOLODetector:
    """
    Thread-safe YOLOv8 detector.
    Lazy-loads model on first call to avoid startup delay.
    """

    _lock = threading.Lock()
    _model = None

    def __init__(self) -> None:
        self._conf = settings.yolo_confidence_threshold
        self._iou = settings.yolo_nms_threshold
        self._device = settings.yolo_device
        self._model_path = settings.yolo_model_path

    # ── Model Loading ──────────────────────────────────────────

    def _load_model(self):
        with self._lock:
            if YOLODetector._model is None:
                try:
                    from ultralytics import YOLO
                    logger.info(f"Loading YOLO model from {self._model_path}")
                    YOLODetector._model = YOLO(self._model_path)
                    logger.success("YOLO model loaded successfully")
                except Exception as exc:
                    logger.error(f"Failed to load YOLO model: {exc}")
                    raise

    @property
    def model(self):
        if YOLODetector._model is None:
            self._load_model()
        return YOLODetector._model

    # ── Inference ─────────────────────────────────────────────

    def detect(
        self,
        frame: np.ndarray,
        camera_id: str,
        frame_id: int = 0,
        classes: Optional[List[int]] = None,
    ) -> DetectionResult:
        """
        Run inference on a single BGR frame.
        Returns DetectionResult with all detections above confidence threshold.
        """
        import time

        target_classes = classes if classes is not None else list(TRACKED_CLASSES.keys())

        t0 = time.perf_counter()
        results = self.model.predict(
            source=frame,
            conf=self._conf,
            iou=self._iou,
            device=self._device,
            classes=target_classes,
            verbose=False,
        )
        inference_ms = (time.perf_counter() - t0) * 1000

        detections: List[Detection] = []
        if results and len(results) > 0:
            for box in results[0].boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                detections.append(
                    Detection(
                        bbox=(x1, y1, x2, y2),
                        class_id=cls_id,
                        label=TRACKED_CLASSES.get(cls_id, f"class_{cls_id}"),
                        confidence=conf,
                        frame_id=frame_id,
                    )
                )

        return DetectionResult(
            frame_id=frame_id,
            camera_id=camera_id,
            detections=detections,
            inference_ms=round(inference_ms, 2),
        )

    def detect_persons(self, frame: np.ndarray, camera_id: str, frame_id: int = 0) -> DetectionResult:
        return self.detect(frame, camera_id, frame_id, classes=[PERSON_CLASS])

    def detect_vehicles(self, frame: np.ndarray, camera_id: str, frame_id: int = 0) -> DetectionResult:
        return self.detect(frame, camera_id, frame_id, classes=list(VEHICLE_CLASSES.keys()))


# Singleton — shared across all stream workers
detector = YOLODetector()
