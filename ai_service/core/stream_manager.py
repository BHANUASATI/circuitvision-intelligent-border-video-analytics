"""
Stream Manager — manages lifecycle of all camera stream workers.
Provides add/remove/status operations consumed by the API layer.
"""
from __future__ import annotations

import asyncio
from typing import Dict, List, Optional

from ai_service.core.stream_worker import CameraConfig, StreamStats, StreamStatus, StreamWorker
from ai_service.utils.logger import logger


class StreamManager:
    """
    Singleton that owns all StreamWorker instances.
    Thread/task-safe via asyncio primitives.
    """

    def __init__(self) -> None:
        self._workers: Dict[str, StreamWorker] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    # ── Public API ────────────────────────────────────────────

    async def start_stream(self, config: CameraConfig) -> bool:
        """
        Start streaming for a camera. Idempotent — returns False if already running.
        """
        async with self._lock:
            if config.camera_id in self._workers:
                logger.warning(f"Stream already running: {config.camera_id}")
                return False

            from ai_service.configs.settings import settings
            if len(self._workers) >= settings.max_concurrent_streams:
                raise RuntimeError(
                    f"Max concurrent streams ({settings.max_concurrent_streams}) reached"
                )

            worker = StreamWorker(config)
            self._workers[config.camera_id] = worker

            task = asyncio.create_task(
                worker.start(),
                name=f"stream-{config.camera_id}",
            )
            self._tasks[config.camera_id] = task

            # Propagate task exceptions to logs
            task.add_done_callback(
                lambda t: self._on_task_done(config.camera_id, t)
            )

            logger.info(f"Stream started: {config.camera_id}")
            return True

    async def stop_stream(self, camera_id: str) -> bool:
        async with self._lock:
            worker = self._workers.get(camera_id)
            if not worker:
                return False
            await worker.stop()
            task = self._tasks.get(camera_id)
            if task and not task.done():
                task.cancel()
            self._workers.pop(camera_id, None)
            self._tasks.pop(camera_id, None)
            logger.info(f"Stream stopped: {camera_id}")
            return True

    async def stop_all(self) -> None:
        camera_ids = list(self._workers.keys())
        for camera_id in camera_ids:
            await self.stop_stream(camera_id)

    def get_stats(self, camera_id: str) -> Optional[StreamStats]:
        worker = self._workers.get(camera_id)
        return worker.stats if worker else None

    def get_all_stats(self) -> List[StreamStats]:
        return [w.stats for w in self._workers.values()]

    def is_running(self, camera_id: str) -> bool:
        return camera_id in self._workers

    # ── Internal ──────────────────────────────────────────────

    def _on_task_done(self, camera_id: str, task: asyncio.Task) -> None:
        exc = task.exception() if not task.cancelled() else None
        if exc:
            logger.error(f"Stream task {camera_id} failed: {exc}")
            # Remove from registry so it can be restarted
            self._workers.pop(camera_id, None)
            self._tasks.pop(camera_id, None)


# Singleton
stream_manager = StreamManager()
