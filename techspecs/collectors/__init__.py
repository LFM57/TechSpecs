"""Hardware collectors aggregation and SpecSnapshot model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from techspecs.collectors.cpu import CPUInfo, collect_cpu_info
from techspecs.collectors.gpu import GPUDevice, GPUInfo, collect_gpu_info
from techspecs.collectors.memory import MemoryInfo, collect_memory_info
from techspecs.collectors.storage import StorageDrive, StorageInfo, collect_storage_info
from techspecs.collectors.system import SystemInfo, collect_system_info


@dataclass
class SpecSnapshot:
    cpu: CPUInfo = field(default_factory=CPUInfo)
    gpu: GPUInfo = field(default_factory=GPUInfo)
    memory: MemoryInfo = field(default_factory=MemoryInfo)
    storage: StorageInfo = field(default_factory=StorageInfo)
    system: SystemInfo = field(default_factory=SystemInfo)
    collected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def collect_specs() -> SpecSnapshot:
    """Collect full hardware specifications across all subsystems."""
    return SpecSnapshot(
        cpu=collect_cpu_info(),
        gpu=collect_gpu_info(),
        memory=collect_memory_info(),
        storage=collect_storage_info(),
        system=collect_system_info(),
    )


__all__ = [
    "CPUInfo",
    "GPUDevice",
    "GPUInfo",
    "MemoryInfo",
    "StorageDrive",
    "StorageInfo",
    "SystemInfo",
    "SpecSnapshot",
    "collect_specs",
    "collect_cpu_info",
    "collect_gpu_info",
    "collect_memory_info",
    "collect_storage_info",
    "collect_system_info",
]
