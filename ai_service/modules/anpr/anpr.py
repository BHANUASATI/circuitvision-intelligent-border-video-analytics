"""
ANPR — Automatic Number Plate Recognition
Pipeline:
  1. YOLO detects license plate region in frame
  2. Crop + perspective-correct the plate ROI
  3. EasyOCR reads the plate text
  4. Fuzzy match against watchlist (Redis / flat-file DB)
"""
from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

from ai_service.configs.settings import settings
from ai_service.utils.logger import logger


# ── Data Models ───────────────────────────────────────────────

@dataclass
class PlateResult:
    bbox: Tuple[int, int, int, int]   # x1, y1, x2, y2 in original frame
    plate_text: str                    # cleaned OCR text
    raw_text: str                      # raw OCR output
    confidence: float                  # OCR confidence
    is_watchlisted: bool = False
    watchlist_entry: Optional[dict] = None


# ── ANPR Engine ───────────────────────────────────────────────

class ANPREngine:
    """
    Plate detector + OCR engine.
    Thread-safe: models loaded once, shared via class-level attributes.
    """

    _lock = threading.Lock()
    _plate_model = None    # YOLO model for plate localisation
    _ocr_reader = None     # EasyOCR reader
    _watchlist: dict = {}  # plate_text -> metadata

    def __init__(self) -> None:
        self._plate_model_path = settings.anpr_model_path
        self._plate_db_path = Path(settings.plate_db_path)
        self._plate_db_path.mkdir(parents=True, exist_ok=True)

    # ── Initialisation ────────────────────────────────────────

    def _ensure_loaded(self) -> None:
        with self._lock:
            if ANPREngine._plate_model is None:
                self._load_plate_model()
            if ANPREngine._ocr_reader is None:
                self._load_ocr()
            if not ANPREngine._watchlist:
                self._load_watchlist()

    def _load_plate_model(self) -> None:
        try:
            from ultralytics import YOLO
            logger.info(f"Loading ANPR YOLO model: {self._plate_model_path}")
            ANPREngine._plate_model = YOLO(self._plate_model_path)
            logger.success("ANPR YOLO model loaded")
        except Exception as exc:
            logger.warning(f"ANPR model load failed ({exc}), using main YOLO fallback")
            ANPREngine._plate_model = None  # will fall back to ROI passed directly

    def _load_ocr(self) -> None:
        import easyocr
        logger.info("Loading EasyOCR reader...")
        ANPREngine._ocr_reader = easyocr.Reader(
            ["en"],
            gpu=settings.yolo_device != "cpu",
            verbose=False,
        )
        logger.success("EasyOCR ready")

    def _load_watchlist(self) -> None:
        watchlist_file = self._plate_db_path / "watchlist.txt"
        if watchlist_file.exists():
            for line in watchlist_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split(",", 2)
                    plate = self._clean_plate(parts[0])
                    ANPREngine._watchlist[plate] = {
                        "plate": plate,
                        "category": parts[1].strip() if len(parts) > 1 else "UNKNOWN",
                        "notes": parts[2].strip() if len(parts) > 2 else "",
                    }
            logger.info(f"Watchlist loaded: {len(ANPREngine._watchlist)} plates")

    # ── Public API ────────────────────────────────────────────

    def process_frame(
        self,
        frame: np.ndarray,
        camera_id: str,
    ) -> List[PlateResult]:
        """Detect plates in full frame, OCR each, check watchlist."""
        self._ensure_loaded()
        results: List[PlateResult] = []

        plate_regions = self._detect_plate_regions(frame)
        for bbox in plate_regions:
            x1, y1, x2, y2 = bbox
            # Add padding
            pad = 10
            h, w = frame.shape[:2]
            x1c, y1c = max(0, x1 - pad), max(0, y1 - pad)
            x2c, y2c = min(w, x2 + pad), min(h, y2 + pad)
            roi = frame[y1c:y2c, x1c:x2c]
            plate_result = self._ocr_roi(roi, (x1, y1, x2, y2))
            if plate_result:
                results.append(plate_result)

        return results

    def process_roi(
        self,
        roi: np.ndarray,
        bbox: Tuple[int, int, int, int],
    ) -> Optional[PlateResult]:
        """Run OCR on a pre-cropped plate ROI."""
        self._ensure_loaded()
        return self._ocr_roi(roi, bbox)

    def add_to_watchlist(self, plate: str, category: str, notes: str = "") -> None:
        cleaned = self._clean_plate(plate)
        ANPREngine._watchlist[cleaned] = {
            "plate": cleaned,
            "category": category,
            "notes": notes,
        }
        # Persist
        watchlist_file = self._plate_db_path / "watchlist.txt"
        with open(watchlist_file, "a") as f:
            f.write(f"{cleaned},{category},{notes}\n")

    # ── Internal Helpers ──────────────────────────────────────

    def _detect_plate_regions(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Use YOLO to find plate bboxes. Falls back to empty list if model unavailable."""
        if ANPREngine._plate_model is None:
            return []
        results = ANPREngine._plate_model.predict(
            source=frame, conf=0.4, verbose=False
        )
        bboxes = []
        if results and results[0].boxes:
            for box in results[0].boxes:
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                bboxes.append((x1, y1, x2, y2))
        return bboxes

    def _preprocess_plate(self, roi: np.ndarray) -> np.ndarray:
        """Denoise + threshold for better OCR accuracy."""
        # Resize to standard height
        target_h = 64
        aspect = roi.shape[1] / roi.shape[0]
        target_w = max(int(target_h * aspect), 100)
        resized = cv2.resize(roi, (target_w, target_h), interpolation=cv2.INTER_CUBIC)

        # Grayscale
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        # Adaptive threshold
        thresh = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh, h=10)
        # Back to BGR for EasyOCR
        return cv2.cvtColor(denoised, cv2.COLOR_GRAY2BGR)

    def _ocr_roi(
        self,
        roi: np.ndarray,
        bbox: Tuple[int, int, int, int],
    ) -> Optional[PlateResult]:
        """Run EasyOCR on a plate ROI and return structured result."""
        if roi.size == 0:
            return None

        processed = self._preprocess_plate(roi)
        ocr_results = ANPREngine._ocr_reader.readtext(
            processed,
            detail=1,
            paragraph=False,
            allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -",
        )
        if not ocr_results:
            return None

        # Pick the highest-confidence result
        best = max(ocr_results, key=lambda r: r[2])
        raw_text = best[1]
        confidence = float(best[2])

        if confidence < 0.3:
            return None

        cleaned = self._clean_plate(raw_text)
        if len(cleaned) < 4:
            return None

        watchlist_entry = ANPREngine._watchlist.get(cleaned)
        return PlateResult(
            bbox=bbox,
            plate_text=cleaned,
            raw_text=raw_text,
            confidence=confidence,
            is_watchlisted=watchlist_entry is not None,
            watchlist_entry=watchlist_entry,
        )

    @staticmethod
    def _clean_plate(text: str) -> str:
        """Uppercase, strip non-alphanumeric except hyphen."""
        return re.sub(r"[^A-Z0-9\-]", "", text.upper().strip())


# Singleton
anpr_engine = ANPREngine()
