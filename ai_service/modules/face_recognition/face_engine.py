"""
Face Recognition Engine — InsightFace (buffalo_l model)
Pipeline:
  1. Detect faces in frame (RetinaFace via InsightFace)
  2. Extract 512-d embedding
  3. Cosine similarity match against enrolled face database
  4. Flag unknown or watchlisted identities
"""
from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from ai_service.configs.settings import settings
from ai_service.utils.logger import logger


# ── Data Models ───────────────────────────────────────────────

@dataclass
class FaceDetection:
    bbox: Tuple[int, int, int, int]     # x1, y1, x2, y2
    landmarks: Optional[np.ndarray]     # 5-point facial landmarks
    det_score: float


@dataclass
class FaceMatch:
    face: FaceDetection
    identity_id: Optional[str]          # None if unknown
    identity_name: Optional[str]
    similarity: float
    is_watchlisted: bool = False
    is_unknown: bool = True


# ── Face Database (in-memory + disk) ─────────────────────────

class FaceDatabase:
    """
    Enrolled face embeddings stored on disk as .npy + metadata JSON.
    Structure:
      /data/face_db/
        embeddings/
          <identity_id>.npy   <- 512-d embedding
        metadata/
          <identity_id>.json  <- name, category, enrolled_at
        watchlist.json        <- [identity_id, ...]
    """

    def __init__(self, db_path: str) -> None:
        self.root = Path(db_path)
        self.emb_dir = self.root / "embeddings"
        self.meta_dir = self.root / "metadata"
        for d in (self.emb_dir, self.meta_dir):
            d.mkdir(parents=True, exist_ok=True)

        self._embeddings: Dict[str, np.ndarray] = {}
        self._metadata: Dict[str, dict] = {}
        self._watchlist: set = set()
        self._load()

    def _load(self) -> None:
        for emb_file in self.emb_dir.glob("*.npy"):
            identity_id = emb_file.stem
            self._embeddings[identity_id] = np.load(str(emb_file))
            meta_file = self.meta_dir / f"{identity_id}.json"
            if meta_file.exists():
                self._metadata[identity_id] = json.loads(meta_file.read_text())

        watchlist_file = self.root / "watchlist.json"
        if watchlist_file.exists():
            self._watchlist = set(json.loads(watchlist_file.read_text()))
        logger.info(f"Face DB loaded: {len(self._embeddings)} identities, "
                    f"{len(self._watchlist)} watchlisted")

    def enroll(
        self,
        identity_id: str,
        embedding: np.ndarray,
        name: str,
        category: str = "enrolled",
    ) -> None:
        self._embeddings[identity_id] = embedding
        np.save(str(self.emb_dir / f"{identity_id}.npy"), embedding)
        meta = {"identity_id": identity_id, "name": name, "category": category}
        self._metadata[identity_id] = meta
        (self.meta_dir / f"{identity_id}.json").write_text(json.dumps(meta, indent=2))
        logger.info(f"Face enrolled: {name} ({identity_id})")

    def add_to_watchlist(self, identity_id: str) -> None:
        self._watchlist.add(identity_id)
        (self.root / "watchlist.json").write_text(
            json.dumps(list(self._watchlist), indent=2)
        )

    def find_match(
        self, embedding: np.ndarray, threshold: float
    ) -> Tuple[Optional[str], float]:
        """Return (identity_id, similarity) or (None, best_score)."""
        if not self._embeddings:
            return None, 0.0

        ids = list(self._embeddings.keys())
        db_matrix = np.stack([self._embeddings[i] for i in ids])  # (N, 512)
        sims = self._cosine_similarity_batch(embedding, db_matrix)
        best_idx = int(np.argmax(sims))
        best_sim = float(sims[best_idx])
        if best_sim >= threshold:
            return ids[best_idx], best_sim
        return None, best_sim

    def get_metadata(self, identity_id: str) -> Optional[dict]:
        return self._metadata.get(identity_id)

    def is_watchlisted(self, identity_id: str) -> bool:
        return identity_id in self._watchlist

    @staticmethod
    def _cosine_similarity_batch(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        q_norm = query / (np.linalg.norm(query) + 1e-6)
        m_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-6)
        return m_norm @ q_norm


# ── Face Recognition Engine ───────────────────────────────────

class FaceRecognitionEngine:
    """
    Thread-safe face recognition using InsightFace.
    """

    _lock = threading.Lock()
    _app = None   # InsightFace FaceAnalysis app

    def __init__(self) -> None:
        self._model_path = settings.face_model_path
        self._threshold = settings.face_recognition_threshold
        self.db = FaceDatabase(settings.face_db_path)

    def _ensure_loaded(self) -> None:
        with self._lock:
            if FaceRecognitionEngine._app is None:
                self._load_model()

    def _load_model(self) -> None:
        try:
            import insightface
            from insightface.app import FaceAnalysis
            logger.info(f"Loading InsightFace model from {self._model_path}")
            app = FaceAnalysis(
                name="buffalo_l",
                root=str(Path(self._model_path).parent),
                providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
            )
            app.prepare(ctx_id=0, det_size=(640, 640))
            FaceRecognitionEngine._app = app
            logger.success("InsightFace loaded")
        except Exception as exc:
            logger.error(f"InsightFace load failed: {exc}")
            raise

    # ── Public API ────────────────────────────────────────────

    def detect_and_recognize(
        self,
        frame: np.ndarray,
        camera_id: str,
    ) -> List[FaceMatch]:
        """Detect all faces in frame and match against enrolled database."""
        self._ensure_loaded()
        app = FaceRecognitionEngine._app

        try:
            faces = app.get(frame)  # returns list of Face objects
        except Exception as exc:
            logger.error(f"Face detection failed: {exc}")
            return []

        matches: List[FaceMatch] = []
        for face in faces:
            bbox = tuple(int(v) for v in face.bbox.astype(int))
            bbox = (bbox[0], bbox[1], bbox[2], bbox[3])
            det = FaceDetection(
                bbox=bbox,
                landmarks=face.kps if hasattr(face, "kps") else None,
                det_score=float(face.det_score),
            )

            if face.embedding is None:
                continue

            identity_id, similarity = self.db.find_match(face.embedding, self._threshold)
            is_unknown = identity_id is None
            is_watchlisted = (not is_unknown) and self.db.is_watchlisted(identity_id)
            meta = self.db.get_metadata(identity_id) if identity_id else None

            matches.append(
                FaceMatch(
                    face=det,
                    identity_id=identity_id,
                    identity_name=meta["name"] if meta else None,
                    similarity=similarity,
                    is_watchlisted=is_watchlisted,
                    is_unknown=is_unknown,
                )
            )

        return matches

    def enroll_face(
        self,
        frame: np.ndarray,
        identity_id: str,
        name: str,
        category: str = "enrolled",
    ) -> bool:
        """Extract embedding from a frame and enroll the face."""
        self._ensure_loaded()
        app = FaceRecognitionEngine._app
        faces = app.get(frame)
        if not faces:
            logger.warning(f"No face found for enrollment: {name}")
            return False
        # Use the largest detected face
        face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        if face.embedding is None:
            return False
        self.db.enroll(identity_id, face.embedding, name, category)
        return True


# Singleton
face_engine = FaceRecognitionEngine()
