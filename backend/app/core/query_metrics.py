from __future__ import annotations

import threading
from dataclasses import dataclass


@dataclass
class QueryMetricSnapshot:
    total_queries: int
    total_duration_ms: float
    average_duration_ms: float
    slow_query_count: int
    slow_threshold_ms: float
    top_slowest: list[dict]


class QueryMetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total_queries = 0
        self._total_duration_ms = 0.0
        self._slow_query_count = 0
        self._top_slowest: list[dict] = []

    def record(self, *, sql: str, duration_ms: float, request_id: str | None, slow_threshold_ms: float) -> None:
        entry = {
            "duration_ms": round(duration_ms, 3),
            "sql": " ".join(sql.strip().split())[:300],
            "request_id": request_id,
        }
        with self._lock:
            self._total_queries += 1
            self._total_duration_ms += duration_ms
            if duration_ms >= slow_threshold_ms:
                self._slow_query_count += 1
            self._top_slowest.append(entry)
            self._top_slowest.sort(key=lambda item: item["duration_ms"], reverse=True)
            self._top_slowest = self._top_slowest[:15]

    def snapshot(self, slow_threshold_ms: float) -> QueryMetricSnapshot:
        with self._lock:
            total_queries = self._total_queries
            total_duration = self._total_duration_ms
            slow_query_count = self._slow_query_count
            top_slowest = list(self._top_slowest)

        avg = (total_duration / total_queries) if total_queries else 0.0
        return QueryMetricSnapshot(
            total_queries=total_queries,
            total_duration_ms=round(total_duration, 3),
            average_duration_ms=round(avg, 3),
            slow_query_count=slow_query_count,
            slow_threshold_ms=slow_threshold_ms,
            top_slowest=top_slowest,
        )

    def reset(self) -> None:
        with self._lock:
            self._total_queries = 0
            self._total_duration_ms = 0.0
            self._slow_query_count = 0
            self._top_slowest = []


query_metrics_registry = QueryMetricsRegistry()
