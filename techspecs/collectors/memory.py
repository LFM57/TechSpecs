"""Memory and swap spec collector."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class MemoryInfo:
    total_bytes: int = 0
    available_bytes: int = 0
    used_bytes: int = 0
    total_gib: float = 0.0
    available_gib: float = 0.0
    used_gib: float = 0.0
    usage_percent: float = 0.0
    swap_total_gib: float = 0.0
    swap_free_gib: float = 0.0
    swap_used_gib: float = 0.0
    has_zram: bool = False
    zram_size_gib: float = 0.0


def collect_memory_info() -> MemoryInfo:
    """Collect memory and swap metrics from /proc/meminfo and sysfs."""
    info = MemoryInfo()
    meminfo_file = Path("/proc/meminfo")

    mem_total_kb = 0
    mem_available_kb = 0
    mem_free_kb = 0
    swap_total_kb = 0
    swap_free_kb = 0

    if meminfo_file.is_file():
        try:
            for line in meminfo_file.read_text().splitlines():
                if ":" not in line:
                    continue
                k, v = line.split(":", 1)
                k = k.strip()
                parts = v.strip().split()
                if not parts:
                    continue
                val = int(parts[0]) if parts[0].isdigit() else 0

                if k == "MemTotal":
                    mem_total_kb = val
                elif k == "MemAvailable":
                    mem_available_kb = val
                elif k == "MemFree":
                    mem_free_kb = val
                elif k == "SwapTotal":
                    swap_total_kb = val
                elif k == "SwapFree":
                    swap_free_kb = val
        except Exception:
            pass

    if mem_available_kb == 0:
        mem_available_kb = mem_free_kb

    info.total_bytes = mem_total_kb * 1024
    info.available_bytes = mem_available_kb * 1024
    info.used_bytes = max(0, info.total_bytes - info.available_bytes)

    info.total_gib = round(info.total_bytes / (1024**3), 2)
    info.available_gib = round(info.available_bytes / (1024**3), 2)
    info.used_gib = round(info.used_bytes / (1024**3), 2)

    if info.total_bytes > 0:
        info.usage_percent = round((info.used_bytes / info.total_bytes) * 100, 1)

    info.swap_total_gib = round((swap_total_kb * 1024) / (1024**3), 2)
    info.swap_free_gib = round((swap_free_kb * 1024) / (1024**3), 2)
    info.swap_used_gib = max(0.0, round(info.swap_total_gib - info.swap_free_gib, 2))

    # Check for ZRAM
    zram_dir = Path("/sys/block/zram0")
    if zram_dir.is_dir():
        info.has_zram = True
        disksize_path = zram_dir / "disksize"
        if disksize_path.is_file():
            try:
                zram_bytes = int(disksize_path.read_text().strip())
                info.zram_size_gib = round(zram_bytes / (1024**3), 2)
            except Exception:
                pass

    return info
