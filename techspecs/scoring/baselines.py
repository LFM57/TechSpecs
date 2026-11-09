"""Reference baselines and comparative ranking engine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BaselineProfile:
    baseline_id: str
    name: str
    category: str
    cpu_spec: str
    gpu_spec: str
    ram_spec: str
    storage_spec: str
    score: float
    description: str


@dataclass
class BaselineComparison:
    baseline_id: str
    name: str
    category: str
    baseline_score: float
    current_score: float
    delta_score: float
    ratio_percent: float
    summary: str


REFERENCE_BASELINES = [
    BaselineProfile(
        baseline_id="budget_netbook",
        name="Budget Chromebook / Netbook",
        category="Ultra-Budget",
        cpu_spec="Intel Celeron N4020 (2C/2T @ 2.8GHz)",
        gpu_spec="Intel UHD Graphics 600",
        ram_spec="4 GB LPDDR4",
        storage_spec="64 GB eMMC Flash",
        score=14.5,
        description="Entry-level netbook for single-window browsing and basic school notes.",
    ),
    BaselineProfile(
        baseline_id="entry_laptop",
        name="Everyday Entry Laptop",
        category="Entry-Level",
        cpu_spec="AMD Athlon Silver 7120U (2C/2T @ 3.5GHz)",
        gpu_spec="AMD Radeon 610M (2 CUs)",
        ram_spec="6 GB LPDDR5",
        storage_spec="128 GB NVMe SSD",
        score=28.5,
        description="Basic modern portable PC for document editing, 1080p streaming, and lightweight tasks.",
    ),
    BaselineProfile(
        baseline_id="mainstream_office",
        name="Modern Mainstream Office PC",
        category="Mid-Range",
        cpu_spec="Intel Core i5-1335U (10C/12T @ 4.6GHz)",
        gpu_spec="Intel Iris Xe Graphics (80 EUs)",
        ram_spec="16 GB DDR4/DDR5",
        storage_spec="512 GB NVMe SSD",
        score=49.0,
        description="Standard workplace machine for heavy web browsing, spreadsheets, and video conferences.",
    ),
    BaselineProfile(
        baseline_id="mainstream_gaming_dev",
        name="Mainstream Gaming & Dev Desktop",
        category="High-Performance",
        cpu_spec="AMD Ryzen 5 7600 (6C/12T @ 5.1GHz)",
        gpu_spec="NVIDIA GeForce RTX 4060 (8 GB)",
        ram_spec="32 GB DDR5-6000",
        storage_spec="1 TB PCIe 4.0 NVMe",
        score=72.0,
        description="High-performance modern setup for 1080p/1440p gaming, containerized dev, and compiling.",
    ),
    BaselineProfile(
        baseline_id="enthusiast_rig",
        name="Enthusiast Gaming & Creator Rig",
        category="Enthusiast",
        cpu_spec="AMD Ryzen 7 7800X3D (8C/16T @ 5.0GHz, 96MB 3D V-Cache)",
        gpu_spec="NVIDIA GeForce RTX 4070 Ti Super (16 GB)",
        ram_spec="32 GB DDR5-6000 CL30",
        storage_spec="2 TB PCIe 4.0 NVMe",
        score=86.5,
        description="Enthusiast powerhouse for ultra-settings 4K gaming, 3D rendering, and local AI pipelines.",
    ),
    BaselineProfile(
        baseline_id="apex_workstation",
        name="Apex AI & 3D Workstation",
        category="Apex Workstation",
        cpu_spec="AMD Ryzen 9 7950X (16C/32T @ 5.7GHz)",
        gpu_spec="NVIDIA GeForce RTX 4090 (24 GB GDDR6X)",
        ram_spec="64 GB DDR5-6000",
        storage_spec="4 TB PCIe 5.0 NVMe",
        score=98.0,
        description="Elite flagship workstation for massive machine learning workloads and industrial simulations.",
    ),
]


def compare_against_baselines(current_score: float) -> list[BaselineComparison]:
    """Compare current computer score against all standard baselines."""
    results: list[BaselineComparison] = []

    for b in REFERENCE_BASELINES:
        delta = round(current_score - b.score, 1)
        ratio = round((current_score / b.score) * 100, 1)

        if abs(delta) <= 2.5:
            summary = "≈ Matches this baseline"
        elif delta > 0:
            summary = f"+{delta:+.1f} pts ({ratio:.0f}% of baseline)"
        else:
            summary = f"{delta:+.1f} pts ({ratio:.0f}% of baseline)"

        results.append(
            BaselineComparison(
                baseline_id=b.baseline_id,
                name=b.name,
                category=b.category,
                baseline_score=b.score,
                current_score=current_score,
                delta_score=delta,
                ratio_percent=ratio,
                summary=summary,
            )
        )

    return results
