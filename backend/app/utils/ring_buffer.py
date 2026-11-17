from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, List


@dataclass
class LogEntry:
    seq: int
    stream: str
    data: str
    ts: float


class RingBuffer:
    def __init__(self, maxlen: int = 2000) -> None:
        self._buf: Deque[LogEntry] = deque(maxlen=maxlen)
        self._seq = 0

    def append(self, stream: str, data: str) -> LogEntry:
        self._seq += 1
        entry = LogEntry(seq=self._seq, stream=stream, data=data, ts=time.time())
        self._buf.append(entry)
        return entry

    def snapshot(self) -> List[LogEntry]:
        return list(self._buf)
