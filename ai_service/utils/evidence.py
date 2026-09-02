"""
Evidence Manager — saves frames/clips with SHA-256 tamper-evident hashing.
Every saved file gets an accompanying .sha256 sidecar for integrity verification.
"""
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from ai_service.configs.settings import settings
from ai_service.utils.logger import logger


class EvidenceManager:
    def __init__(self) -> None:
        self.base_path = Path(settings.evidence_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    # ── Public API ─────────────────────────────────────────────

    def save_frame(
        self,
        frame: np.ndarray,
        camera_id: str,
        event_type: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Save a single frame as JPEG evidence with SHA-256 hash."""
        evidence_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        dir_path = self._event_dir(camera_id, event_type, timestamp)

        filename = f"{evidence_id}.jpg"
        file_path = dir_path / filename

        # Encode and write
        success, buffer = cv2.imencode(
            ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95]
        )
        if not success:
            raise RuntimeError("Failed to encode frame as JPEG")

        file_path.write_bytes(buffer.tobytes())

        # Compute hash
        file_hash = self._sha256(file_path)

        # Write sidecar
        sidecar = {
            "evidence_id": evidence_id,
            "camera_id": camera_id,
            "event_type": event_type,
            "timestamp": timestamp.isoformat(),
            "filename": filename,
            "sha256": file_hash,
            "metadata": metadata or {},
        }
        self._write_sidecar(dir_path / f"{evidence_id}.json", sidecar)

        logger.info(
            f"Evidence saved | id={evidence_id} camera={camera_id} "
            f"event={event_type} hash={file_hash[:16]}..."
        )
        return sidecar

    def verify_evidence(self, evidence_id: str, camera_id: str, event_type: str) -> bool:
        """Verify the integrity of a saved evidence file against its sidecar hash."""
        # Search for the sidecar
        for sidecar_path in self.base_path.rglob(f"{evidence_id}.json"):
            sidecar = json.loads(sidecar_path.read_text())
            img_path = sidecar_path.parent / sidecar["filename"]
            if not img_path.exists():
                logger.warning(f"Evidence file missing: {img_path}")
                return False
            current_hash = self._sha256(img_path)
            return current_hash == sidecar["sha256"]
        logger.warning(f"Sidecar not found for evidence_id={evidence_id}")
        return False

    # ── Helpers ────────────────────────────────────────────────

    def _event_dir(self, camera_id: str, event_type: str, ts: datetime) -> Path:
        path = (
            self.base_path
            / camera_id
            / event_type
            / ts.strftime("%Y/%m/%d/%H")
        )
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _write_sidecar(path: Path, data: dict) -> None:
        path.write_text(json.dumps(data, indent=2))


# Singleton
evidence_manager = EvidenceManager()
