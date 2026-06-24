from __future__ import annotations
import time

EE_GAP_WEIGHTS: dict[str, float] = {"HIGH": 1.0, "MED": 0.5, "LOW": 0.0}


def compute_traction(percent_funded: float, deadline_ts: int, launched_ts: int) -> float:
    now = time.time()
    total_secs = deadline_ts - launched_ts
    if total_secs <= 0:
        return 0.0
    elapsed_frac = max((now - launched_ts) / total_secs, 0.05)
    return (percent_funded / 100.0) / elapsed_frac


def days_remaining(deadline_ts: int) -> int:
    return max(0, int((deadline_ts - time.time()) / 86400))


def composite_score(traction: float, ee_gap: str, confidence: float) -> float:
    return min(traction, 5.0) * EE_GAP_WEIGHTS.get(ee_gap, 0.0) * confidence
