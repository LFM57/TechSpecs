"""Scoring engine: computes power scores, workload ratings, and bottlenecks."""

from __future__ import annotations

import math
from techspecs.collectors import SpecSnapshot
from techspecs.scoring.models import (
    BottleneckWarning,
    ComponentScores,
    PowerReport,
    RatingTier,
    WorkloadScores,
)

TIERS = [
    RatingTier(
        tier_id="ultra_budget",
        name="Ultra-Budget / Minimal",
        verdict="Very Weak",
        min_score=0.0,
        max_score=25.0,
        description="Suitable for basic terminal commands, text editing, and lightweight single-tab browsing. Multi-tasking or modern multimedia will experience noticeable lag.",
        badge_style="red",
    ),
    RatingTier(
        tier_id="entry_level",
        name="Entry-Level / Everyday",
        verdict="Modest / Entry-Level",
        min_score=25.0,
        max_score=45.0,
        description="Handles daily office tasks, 1080p video streaming, light web multitasking, and lightweight indie/retro games.",
        badge_style="yellow",
    ),
    RatingTier(
        tier_id="mid_range",
        name="Solid Mid-Range",
        verdict="Solid Mid-Range",
        min_score=45.0,
        max_score=65.0,
        description="Great for mainstream multitasking, 1080p gaming, web/app software development, photo editing, and general productivity.",
        badge_style="cyan",
    ),
    RatingTier(
        tier_id="performance",
        name="High-Performance",
        verdict="Powerful",
        min_score=65.0,
        max_score=80.0,
        description="Fast and responsive for demanding workloads: 1440p gaming, large software builds, local Docker workflows, and 4K media work.",
        badge_style="green",
    ),
    RatingTier(
        tier_id="enthusiast",
        name="Enthusiast / Creator",
        verdict="Very Powerful",
        min_score=80.0,
        max_score=92.0,
        description="Exceptional performance for 4K high-FPS gaming, 3D animation, deep learning inference, and compile-intensive codebases.",
        badge_style="magenta",
    ),
    RatingTier(
        tier_id="apex_workstation",
        name="Apex Workstation",
        verdict="Apex Workstation",
        min_score=92.0,
        max_score=100.0,
        description="Elite multi-core workstation / server grade computing power for massive dataset crunching, AI model training, and heavy engineering simulations.",
        badge_style="bold magenta",
    ),
]


def _get_tier(score: float) -> RatingTier:
    """Determine rating tier from composite score."""
    clamped = max(0.0, min(100.0, score))
    for t in TIERS:
        if t.min_score <= clamped <= t.max_score:
            return t
    return TIERS[-1]


def compute_cpu_score(spec: SpecSnapshot) -> float:
    """Compute CPU power score on 0-100 scale."""
    cpu = spec.cpu
    threads = max(1, cpu.logical_threads)
    cores = max(1, cpu.physical_cores)

    # Effective core capability with diminishing returns (Amdahl law inspired)
    # 2 cores -> ~1.8, 4 cores -> ~3.4, 8 cores -> ~6.5, 16 cores -> ~11.5, 32 cores -> ~18.0
    effective_core_weight = (cores ** 0.82) + (max(0, threads - cores) * 0.3)

    # Reference 8 cores / 16 threads = ~7.5 effective cores = 50 base points
    base_score = 12.0 + (effective_core_weight * 5.0)

    # Clock frequency adjustment
    max_mhz = cpu.max_mhz or cpu.current_mhz or 2500.0
    # Normalize around 4.5 GHz boost standard
    freq_multiplier = (max_mhz / 4500.0) ** 0.65
    score = base_score * freq_multiplier

    # Architecture generation factor
    arch = cpu.arch_family.lower()
    if "zen 5" in arch or "arrow lake" in arch:
        score *= 1.15
    elif "zen 4" in arch or "raptor lake" in arch or "m3" in arch or "m4" in arch:
        score *= 1.08
    elif "zen 3" in arch or "alder lake" in arch or "m1" in arch or "m2" in arch:
        score *= 1.00
    elif "zen 2" in arch or "tiger lake" in arch:
        score *= 0.88
    elif "zen" in arch or "skylake" in arch or "comet lake" in arch:
        score *= 0.78
    elif "celeron" in arch or "low-power" in arch:
        score *= 0.65

    # Cache bonus/penalty
    l3_mb = (cpu.l3_cache_kb or 0) / 1024.0
    if l3_mb >= 32.0:
        score += 6.0
    elif l3_mb >= 16.0:
        score += 3.0
    elif l3_mb < 3.0 and l3_mb > 0:
        score -= 4.0
    elif l3_mb == 0 and cores > 2:
        score -= 6.0

    # Modern instruction set extensions bonus
    if cpu.has_avx2:
        score += 3.0
    if cpu.has_avx512:
        score += 5.0
    if cpu.has_fma:
        score += 1.5

    return round(max(5.0, min(100.0, score)), 1)


def compute_gpu_score(spec: SpecSnapshot) -> float:
    """Compute GPU power score on 0-100 scale."""
    gpu_info = spec.gpu
    primary = gpu_info.primary_gpu

    if not primary:
        return 10.0

    lower_name = primary.name.lower()
    vendor = primary.vendor.lower()
    vram_mb = primary.vram_mb or 0
    is_igpu = primary.is_integrated

    # Determine base score by GPU model class
    if not is_igpu:
        # Dedicated GPUs
        if any(x in lower_name for x in ("4090", "5090", "6000 ada", "h100", "a100")):
            base = 98.0
        elif any(x in lower_name for x in ("4080", "7900 xtx", "7900 xt")):
            base = 90.0
        elif any(x in lower_name for x in ("4070 ti", "4070", "7800 xt", "6950 xt")):
            base = 82.0
        elif any(x in lower_name for x in ("4060 ti", "4060", "7700 xt", "6700 xt", "3070")):
            base = 72.0
        elif any(x in lower_name for x in ("3060", "6600", "7600", "2060", "arc a770", "arc a750")):
            base = 62.0
        elif any(x in lower_name for x in ("3050", "1660", "1650", "6500 xt", "6400", "arc a380")):
            base = 48.0
        elif any(x in lower_name for x in ("1050", "rx 580", "rx 570", "rx 560", "gt 1030")):
            base = 36.0
        else:
            base = 52.0  # Generic modern discrete GPU

        # VRAM adjustment
        if vram_mb >= 24000:
            base += 4.0
        elif vram_mb >= 16000:
            base += 2.0
        elif vram_mb < 6000 and vram_mb > 0:
            base -= 6.0
    else:
        # Integrated GPUs
        if any(x in lower_name for x in ("890m", "880m", "arc graphics 140v", "arc 8-core")):
            base = 48.0
        elif any(x in lower_name for x in ("780m", "680m", "arc graphics 130v")):
            base = 42.0
        elif any(x in lower_name for x in ("660m", "iris xe", "vega 8", "vega 7")):
            base = 32.0
        elif any(x in lower_name for x in ("610m", "mendocino", "vega 6", "vega 3")):
            base = 22.0
        elif any(x in lower_name for x in ("uhd 770", "uhd 750", "uhd 730")):
            base = 25.0
        elif any(x in lower_name for x in ("uhd 630", "uhd 620", "hd graphics")):
            base = 18.0
        elif any(x in lower_name for x in ("uhd 600", "uhd 605", "hd 4000", "hd 3000")):
            base = 12.0
        else:
            base = 20.0

    return round(max(5.0, min(100.0, base)), 1)


def compute_memory_score(spec: SpecSnapshot) -> float:
    """Compute RAM power score on 0-100 scale."""
    ram = spec.memory
    total_gib = ram.total_gib

    # Capacity non-linear utility curve
    if total_gib <= 2.5:
        score = 8.0
    elif total_gib <= 4.5:
        score = 18.0
    elif total_gib <= 6.5:
        # 6 GB (like Athlon laptops)
        score = 30.0
    elif total_gib <= 8.5:
        score = 42.0
    elif total_gib <= 12.5:
        score = 58.0
    elif total_gib <= 16.5:
        score = 72.0
    elif total_gib <= 24.5:
        score = 83.0
    elif total_gib <= 32.5:
        score = 92.0
    elif total_gib <= 64.5:
        score = 98.0
    else:
        score = 100.0

    # ZRAM / Swap availability cushion
    if ram.has_zram:
        score += 2.0
    elif ram.swap_total_gib > 0:
        score += 1.0

    return round(max(5.0, min(100.0, score)), 1)


def compute_storage_score(spec: SpecSnapshot) -> float:
    """Compute Storage power score on 0-100 scale."""
    storage = spec.storage
    primary = storage.primary_drive

    if not primary:
        base = 50.0
    elif primary.is_nvme:
        base = 86.0
    elif primary.is_ssd:
        base = 65.0
    elif "emmc" in primary.media_type.lower():
        base = 45.0
    else:
        # Rotational HDD
        base = 22.0

    # Total capacity factor
    total_gib = storage.total_disk_gib
    if total_gib >= 2000.0:
        base += 12.0
    elif total_gib >= 900.0:
        base += 8.0
    elif total_gib >= 450.0:
        base += 4.0
    elif total_gib < 150.0 and total_gib > 0:
        base -= 4.0

    return round(max(5.0, min(100.0, base)), 1)


def compute_overall_score(components: ComponentScores) -> float:
    """Compute weighted composite score with harmonic bottleneck penalty."""
    # Weights: CPU (38%), GPU (32%), RAM (18%), Storage (12%)
    weighted = (
        components.cpu * 0.38
        + components.gpu * 0.32
        + components.memory * 0.18
        + components.storage * 0.12
    )

    # Bottleneck dampening: If the lowest component is substantially behind the rest,
    # the entire user experience is dragged down.
    min_comp = min(components.cpu, components.gpu, components.memory, components.storage)
    avg_comp = (components.cpu + components.gpu + components.memory + components.storage) / 4.0

    delta = avg_comp - min_comp
    if delta > 25.0:
        # Apply progressive penalty up to 8%
        penalty = min(8.0, (delta - 25.0) * 0.25)
        weighted -= penalty

    return round(max(5.0, min(100.0, weighted)), 1)


def compute_workload_scores(components: ComponentScores) -> WorkloadScores:
    """Compute specialized scores for common workloads."""
    # Office / Everyday: CPU 45% + RAM 30% + Storage 20% + GPU 5%
    office = (
        components.cpu * 0.45
        + components.memory * 0.30
        + components.storage * 0.20
        + components.gpu * 0.05
    )

    # Gaming: GPU 60% + CPU 20% + RAM 15% + Storage 5%
    gaming = (
        components.gpu * 0.60
        + components.cpu * 0.20
        + components.memory * 0.15
        + components.storage * 0.05
    )

    # Software Engineering: CPU 45% + RAM 30% + Storage 20% + GPU 5%
    dev = (
        components.cpu * 0.45
        + components.memory * 0.30
        + components.storage * 0.20
        + components.gpu * 0.05
    )

    # AI & Machine Learning: GPU 55% + RAM 25% + CPU 20%
    ai = (
        components.gpu * 0.55
        + components.memory * 0.25
        + components.cpu * 0.20
    )

    return WorkloadScores(
        office=round(max(5.0, min(100.0, office)), 1),
        gaming=round(max(5.0, min(100.0, gaming)), 1),
        development=round(max(5.0, min(100.0, dev)), 1),
        ai_ml=round(max(5.0, min(100.0, ai)), 1),
    )


def detect_bottlenecks(spec: SpecSnapshot, components: ComponentScores) -> list[BottleneckWarning]:
    """Detect hardware bottlenecks and provide upgrade recommendations."""
    warnings: list[BottleneckWarning] = []

    # RAM bottleneck
    if components.memory <= 35.0:
        warnings.append(
            BottleneckWarning(
                component="Memory (RAM)",
                severity="High" if components.memory <= 20.0 else "Medium",
                description=f"System has only {spec.memory.total_gib:.1f} GiB RAM. Modern browser multi-tabbing and applications will experience swap thrashing.",
                recommendation="Upgrading to at least 16 GB RAM will dramatically improve multitasking responsiveness (+15-20 pts to overall performance).",
            )
        )

    # GPU bottleneck
    if components.gpu <= 25.0 and spec.gpu.primary_gpu and spec.gpu.primary_gpu.is_integrated:
        warnings.append(
            BottleneckWarning(
                component="Graphics (GPU)",
                severity="Medium",
                description=f"Integrated graphics ({spec.gpu.primary_gpu.name}) offers entry-level 3D capability.",
                recommendation="Suitable for video playback and light 2D tasks. Demanding 3D games and local LLM execution will require a dedicated GPU.",
            )
        )

    # CPU core bottleneck
    if spec.cpu.physical_cores <= 2:
        warnings.append(
            BottleneckWarning(
                component="CPU Cores",
                severity="Medium",
                description=f"Processor has only {spec.cpu.physical_cores} physical cores ({spec.cpu.logical_threads} threads).",
                recommendation="Heavy multitasking or background compile tasks will saturate all available cores.",
            )
        )

    # Storage type bottleneck
    if spec.storage.primary_drive and not spec.storage.primary_drive.is_ssd:
        warnings.append(
            BottleneckWarning(
                component="Storage",
                severity="High",
                description="Primary drive is a rotational HDD, which is the single slowest component for system boot and app loading.",
                recommendation="Replacing the HDD with a modern NVMe or SATA SSD will make the system feel several times faster.",
            )
        )

    return warnings


def evaluate_specs(spec: SpecSnapshot) -> PowerReport:
    """Run full evaluation pipeline on collected specs."""
    cpu_s = compute_cpu_score(spec)
    gpu_s = compute_gpu_score(spec)
    mem_s = compute_memory_score(spec)
    dsk_s = compute_storage_score(spec)

    components = ComponentScores(
        cpu=cpu_s,
        gpu=gpu_s,
        memory=mem_s,
        storage=dsk_s,
    )

    overall = compute_overall_score(components)
    tier = _get_tier(overall)
    workloads = compute_workload_scores(components)
    bottlenecks = detect_bottlenecks(spec, components)

    return PowerReport(
        overall_score=overall,
        tier=tier,
        components=components,
        workloads=workloads,
        bottlenecks=bottlenecks,
        spec=spec,
    )
