"""Empirical micro-benchmark engine for rapid system calibration."""

from __future__ import annotations

import hashlib
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    single_score: float = 0.0
    multi_score: float = 0.0
    memory_score: float = 0.0
    overall_benchmark_score: float = 0.0
    multi_thread_speedup: float = 1.0
    single_ops_per_sec: float = 0.0
    multi_ops_per_sec: float = 0.0
    mem_bandwidth_gbps: float = 0.0
    duration_seconds: float = 0.0


def _compute_chunk(iterations: int) -> int:
    """Worker task computing hash chain and transcendental math."""
    h = b"benchmark_salt_init"
    acc = 0.0
    for i in range(iterations):
        h = hashlib.sha256(h).digest()
        acc += math.sin(i)
    return len(h) + int(acc * 0.0)


def run_single_core_bench(iterations: int = 400_000) -> tuple[float, float]:
    """Run single-core workload. Returns (ops_per_sec, elapsed)."""
    t0 = time.perf_counter()
    _compute_chunk(iterations)
    dur = max(1e-6, time.perf_counter() - t0)
    ops = iterations / dur
    return ops, dur


def run_multi_core_bench(workers: int, iterations_per_worker: int = 300_000) -> tuple[float, float]:
    """Run parallel multi-core workload. Returns (total_ops_per_sec, elapsed)."""
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_compute_chunk, iterations_per_worker) for _ in range(workers)]
        for f in futures:
            f.result()
    dur = max(1e-6, time.perf_counter() - t0)
    total_ops = (iterations_per_worker * workers) / dur
    return total_ops, dur


def run_memory_bench(chunk_size_mb: int = 24, passes: int = 8) -> tuple[float, float]:
    """Run memory read/write streaming benchmark. Returns (gb_per_sec, elapsed)."""
    size_bytes = chunk_size_mb * 1024 * 1024
    buf = bytearray(size_bytes)
    t0 = time.perf_counter()
    for _ in range(passes):
        buf[::2] = buf[1::2]
    dur = max(1e-6, time.perf_counter() - t0)
    gb_transferred = (size_bytes * passes) / (1024**3)
    gbps = gb_transferred / dur
    return gbps, dur


def run_quick_benchmark(workers: int | None = None) -> BenchmarkResult:
    """Execute complete micro-benchmark in ~2 seconds."""
    num_workers = workers or os.cpu_count() or 1
    t_start = time.perf_counter()

    # 1. Single core test
    single_ops, single_dur = run_single_core_bench(iterations=400_000)

    # 2. Multi core test
    multi_ops, multi_dur = run_multi_core_bench(workers=num_workers, iterations_per_worker=250_000)

    # 3. Memory test
    mem_gbps, mem_dur = run_memory_bench(chunk_size_mb=20, passes=8)

    total_dur = round(time.perf_counter() - t_start, 2)

    # Calibration scale:
    # Single-core: 4.5M ops/s = 100 pts. 1.7M ops/s = ~42 pts.
    single_score = min(100.0, max(5.0, (single_ops / 4_500_000.0) * 100.0))

    # Multi-core: 32-thread modern monster (~45M ops/s) = 100 pts.
    # 2 cores (~3.4M ops/s) = ~22 pts.
    multi_score = min(100.0, max(5.0, (multi_ops / 35_000_000.0) * 100.0))

    # Memory: 5.0 GB/s in Python = 100 pts.
    mem_score = min(100.0, max(5.0, (mem_gbps / 4.0) * 100.0))

    speedup = round(multi_ops / max(1.0, single_ops), 2)

    # Composite benchmark score: 35% single + 45% multi + 20% mem
    composite = round(
        single_score * 0.35 + multi_score * 0.45 + mem_score * 0.20,
        1,
    )

    return BenchmarkResult(
        single_score=round(single_score, 1),
        multi_score=round(multi_score, 1),
        memory_score=round(mem_score, 1),
        overall_benchmark_score=composite,
        multi_thread_speedup=speedup,
        single_ops_per_sec=round(single_ops, 0),
        multi_ops_per_sec=round(multi_ops, 0),
        mem_bandwidth_gbps=round(mem_gbps, 2),
        duration_seconds=total_dur,
    )
