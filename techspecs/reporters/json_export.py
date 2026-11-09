"""JSON exporter for power reports and hardware specs."""

from __future__ import annotations

import dataclasses
import json
from typing import Any

from techspecs.scoring import BenchmarkResult, PowerReport, compare_against_baselines


def _to_serializable(obj: Any) -> Any:
    """Convert dataclasses and complex structures into JSON-friendly dicts."""
    if dataclasses.is_dataclass(obj):
        return {k: _to_serializable(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, list):
        return [_to_serializable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    return obj


def generate_json_report(report: PowerReport, bench: BenchmarkResult | None = None) -> str:
    """Serialize full evaluation report and baselines to formatted JSON."""
    baselines_comp = compare_against_baselines(report.overall_score)

    payload = {
        "overall_score": report.overall_score,
        "rating_tier": {
            "tier_id": report.tier.tier_id,
            "name": report.tier.name,
            "verdict": report.tier.verdict,
            "description": report.tier.description,
        },
        "components": dataclasses.asdict(report.components),
        "workloads": dataclasses.asdict(report.workloads),
        "bottlenecks": [dataclasses.asdict(b) for b in report.bottlenecks],
        "baselines_comparison": [dataclasses.asdict(b) for b in baselines_comp],
        "specifications": {
            "system": dataclasses.asdict(report.spec.system),
            "cpu": dataclasses.asdict(report.spec.cpu),
            "gpu": {
                "has_discrete_gpu": report.spec.gpu.has_discrete_gpu,
                "total_vram_mb": report.spec.gpu.total_vram_mb,
                "primary": dataclasses.asdict(report.spec.gpu.primary_gpu) if report.spec.gpu.primary_gpu else None,
                "devices": [dataclasses.asdict(d) for d in report.spec.gpu.devices],
            },
            "memory": dataclasses.asdict(report.spec.memory),
            "storage": {
                "total_disk_gib": report.spec.storage.total_disk_gib,
                "has_nvme": report.spec.storage.has_nvme,
                "has_ssd": report.spec.storage.has_ssd,
                "primary": dataclasses.asdict(report.spec.storage.primary_drive) if report.spec.storage.primary_drive else None,
                "drives": [dataclasses.asdict(d) for d in report.spec.storage.drives],
            },
        },
    }

    if bench:
        payload["benchmark"] = dataclasses.asdict(bench)

    return json.dumps(payload, indent=2)
