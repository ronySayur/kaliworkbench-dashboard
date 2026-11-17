from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict
from dataclasses import asdict
from typing import Any

from fastapi import WebSocket

from app.config import settings
from app.utils.ring_buffer import LogEntry, RingBuffer


class JobStream:
    def __init__(self, job_id: int) -> None:
        self.job_id = job_id
        self.buffer = RingBuffer(maxlen=settings.log_ring_size)
        self.subscribers: set[WebSocket] = set()
        self._queue: list[dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._flusher_task: asyncio.Task[None] | None = None
        self.closed = False

    async def start(self) -> None:
        if self._flusher_task is None:
            self._flusher_task = asyncio.create_task(self._flush_loop())

    async def stop(self) -> None:
        self.closed = True
        if self._flusher_task:
            self._flusher_task.cancel()
            try:
                await self._flusher_task
            except asyncio.CancelledError:
                pass
            self._flusher_task = None
        await self.flush()

    async def subscribe(self, ws: WebSocket) -> None:
        async with self._lock:
            self.subscribers.add(ws)

    async def unsubscribe(self, ws: WebSocket) -> None:
        async with self._lock:
            self.subscribers.discard(ws)

    def append_log(self, stream: str, data: str) -> None:
        entry = self.buffer.append(stream, data)
        self._queue.append(
            {
                "type": "log",
                "job_id": self.job_id,
                "seq": entry.seq,
                "stream": entry.stream,
                "data": entry.data,
                "ts": entry.ts,
            }
        )

    def queue_event(self, event: dict[str, Any]) -> None:
        if "job_id" not in event:
            event["job_id"] = self.job_id
        if "ts" not in event:
            event["ts"] = time.time()
        self._queue.append(event)

    async def _flush_loop(self) -> None:
        interval = max(settings.log_batch_ms, 50) / 1000.0
        try:
            while not self.closed:
                await asyncio.sleep(interval)
                await self.flush()
        except asyncio.CancelledError:
            pass

    async def flush(self) -> None:
        if not self._queue:
            return
        batch = self._queue
        self._queue = []
        payload = json.dumps({"type": "batch", "events": batch})
        async with self._lock:
            targets = list(self.subscribers)
        if not targets:
            return
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self.subscribers.discard(ws)

    def replay_events(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "log",
                "job_id": self.job_id,
                "seq": e.seq,
                "stream": e.stream,
                "data": e.data,
                "ts": e.ts,
            }
            for e in self.buffer.snapshot()
        ]


class WSManager:
    def __init__(self) -> None:
        self._streams: dict[int, JobStream] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(self, job_id: int) -> JobStream:
        async with self._lock:
            stream = self._streams.get(job_id)
            if stream is None:
                stream = JobStream(job_id)
                self._streams[job_id] = stream
                await stream.start()
            return stream

    async def get(self, job_id: int) -> JobStream | None:
        async with self._lock:
            return self._streams.get(job_id)

    async def remove(self, job_id: int) -> None:
        async with self._lock:
            stream = self._streams.pop(job_id, None)
        if stream:
            await stream.stop()


ws_manager = WSManager()
