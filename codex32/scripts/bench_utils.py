"""Tiny, dependency-free micro-benchmarks for Codex-32.

This is intentionally simple: it's meant for quick local validation when making
small efficiency improvements (no external profilers required).

Usage (optional):
    python -m scripts.bench_utils

Notes:
- Runs in-process and uses perf_counter.
- Focuses on hot code paths that are easy to accidentally regress:
  - registry stats (O(n) counts)
  - guide/status computation
  - incident tail reading
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Any

from app.bot_registry import SecureRegistry, BotStatus
from app.supervisor import IncidentLog, Incident


def _bench(name: str, fn: Callable[[], Any], rounds: int = 5000) -> Dict[str, Any]:
    t0 = time.perf_counter()
    for _ in range(rounds):
        fn()
    t1 = time.perf_counter()
    total = t1 - t0
    return {
        "name": name,
        "rounds": rounds,
        "total_s": total,
        "per_call_us": (total / rounds) * 1_000_000,
    }


def _seed_registry(registry: SecureRegistry, n: int = 250) -> None:
    # Populate registry._cache directly to avoid disk I/O in the benchmark.
    registry._cache = {}
    for i in range(n):
        bot_id = f"bot-{i}"
        registry._cache[bot_id] = {
            "id": bot_id,
            "name": f"Bot {i}",
            "status": (BotStatus.RUNNING.value if i % 5 == 0 else BotStatus.CREATED.value),
        }


def _seed_incidents(path: Path, n: int = 1000) -> None:
    log = IncidentLog(str(path))
    # overwrite
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    for i in range(n):
        log.append(
            Incident(
                incident_id=f"inc-{i}",
                bot_id=f"bot-{i%10}",
                bot_name=f"Bot {i%10}",
                kind="test",
                message="benchmark",
                data={"i": i, "ts": datetime.now().isoformat()},
            )
        )


def main() -> None:
    registry = SecureRegistry(registry_file=":memory:")
    _seed_registry(registry, n=500)

    incident_path = Path(".bench") / "incidents.jsonl"
    _seed_incidents(incident_path, n=2000)
    incident_log = IncidentLog(str(incident_path))

    results = []

    results.append(_bench("registry.get_registry_stats", registry.get_registry_stats, rounds=5000))
    results.append(_bench("incident_log.tail(200)", lambda: incident_log.tail(limit=200), rounds=200))

    # pretty print
    print("\n".join(
        f"{r['name']}: {r['per_call_us']:.2f} µs/call (rounds={r['rounds']}, total={r['total_s']:.3f}s)"
        for r in results
    ))


if __name__ == "__main__":
    main()
