"""Latency aggregation utilities."""

import statistics
from typing import List


def compute_latency_stats(latencies: List[float]) -> dict:
    """Compute latency statistics from a list of latency values (seconds).

    Returns:
        dict with p50, p95, p99, mean, min, max, count
    """
    if not latencies:
        return {"p50": 0, "p95": 0, "p99": 0, "mean": 0, "min": 0, "max": 0, "count": 0}

    sorted_lat = sorted(latencies)
    n = len(sorted_lat)

    def percentile(p: float) -> float:
        k = (n - 1) * (p / 100)
        f = int(k)
        c = f + 1 if f + 1 < n else f
        d = k - f
        return round(sorted_lat[f] + d * (sorted_lat[c] - sorted_lat[f]), 3)

    return {
        "p50": percentile(50),
        "p95": percentile(95),
        "p99": percentile(99),
        "mean": round(statistics.mean(latencies), 3),
        "min": round(min(latencies), 3),
        "max": round(max(latencies), 3),
        "count": n,
    }
