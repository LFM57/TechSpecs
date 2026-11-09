"""Markdown report exporter."""

from __future__ import annotations

from techspecs.scoring import BenchmarkResult, PowerReport, compare_against_baselines


def generate_markdown_report(report: PowerReport, bench: BenchmarkResult | None = None) -> str:
    """Generate a GitHub-flavored Markdown performance and spec audit report."""
    spec = report.spec
    comps = report.components
    work = report.workloads
    baselines = compare_against_baselines(report.overall_score)

    lines: list[str] = [
        f"# Hardware Specification & Power Score Audit",
        f"",
        f"**System**: {spec.system.manufacturer} {spec.system.product_name} ({spec.system.chassis_type})  ",
        f"**OS / Kernel**: {spec.system.os_name} {spec.system.os_version} | Kernel: `{spec.system.kernel}`  ",
        f"**Audit Date**: {spec.collected_at}",
        f"",
        f"---",
        f"",
        f"## Overall Power Verdict: **{report.tier.verdict}**",
        f"",
        f"> **Overall Composite Score: {report.overall_score} / 100**  ",
        f"> **Tier**: {report.tier.name}  ",
        f"> *{report.tier.description}*",
        f"",
        f"### Component Score Breakdown",
        f"",
        f"| Component | Score (0-100) | Specification Summary |",
        f"|---|---|---|",
        f"| **CPU** | **{comps.cpu}** | {spec.cpu.model_name} ({spec.cpu.physical_cores}C/{spec.cpu.logical_threads}T, {spec.cpu.max_mhz or 'N/A'} MHz boost) |",
        f"| **GPU** | **{comps.gpu}** | {spec.gpu.primary_gpu.name if spec.gpu.primary_gpu else 'None'} ({'iGPU' if (spec.gpu.primary_gpu and spec.gpu.primary_gpu.is_integrated) else 'dGPU'}, {spec.gpu.total_vram_mb} MB VRAM) |",
        f"| **RAM** | **{comps.memory}** | {spec.memory.total_gib} GiB Total (Swap: {spec.memory.swap_total_gib} GiB {'with ZRAM' if spec.memory.has_zram else ''}) |",
        f"| **Storage** | **{comps.storage}** | {spec.storage.primary_drive.media_type if spec.storage.primary_drive else 'Drive'} ({spec.storage.total_disk_gib} GiB capacity) |",
        f"",
        f"### Workload Suitability Ratings",
        f"",
        f"| Workload Profile | Rating (0-100) | Suitability |",
        f"|---|---|---|",
        f"| **Daily Office / Productivity** | **{work.office}** | {'Optimal' if work.office >= 65 else 'Capable' if work.office >= 35 else 'Minimal'} |",
        f"| **3D Gaming & Graphics** | **{work.gaming}** | {'High-FPS 1440p/4K' if work.gaming >= 75 else '1080p Mainstream' if work.gaming >= 50 else 'Entry / Indie 2D' if work.gaming >= 20 else 'Not Recommended'} |",
        f"| **Software Development** | **{work.development}** | {'Fast Large Builds & Docker' if work.development >= 70 else 'General Web/Scripting' if work.development >= 40 else 'Lightweight Code Editing'} |",
        f"| **AI & Machine Learning** | **{work.ai_ml}** | {'Local LLM Fine-Tuning' if work.ai_ml >= 75 else 'Quantized Small Model Inference' if work.ai_ml >= 40 else 'Cloud/API Delegated Only'} |",
        f"",
        f"---",
        f"",
        f"## Baseline Comparisons",
        f"",
        f"| Reference Tier | Hardware Baseline | Score | Comparison vs Your PC |",
        f"|---|---|---|---|",
    ]

    for b in baselines:
        lines.append(f"| **{b.category}** | {b.name} | {b.baseline_score} | {b.summary} |")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## System Bottlenecks & Upgrade Advice",
        f"",
    ])

    if report.bottlenecks:
        for bn in report.bottlenecks:
            lines.append(f"> [!WARNING] **{bn.component} ({bn.severity} Impact)**: {bn.description}")
            lines.append(f"> ")
            lines.append(f"> **Recommendation**: {bn.recommendation}")
            lines.append(f"")
    else:
        lines.append(f"> [!NOTE] No major component bottlenecks detected! The system hardware is well balanced.")
        lines.append(f"")

    if bench:
        lines.extend([
            f"---",
            f"",
            f"## Empirical Micro-Benchmark Results",
            f"",
            f"- **Benchmark Composite Score**: **{bench.overall_benchmark_score} / 100**",
            f"- **Single-Core Speed**: {bench.single_ops_per_sec:,.0f} ops/sec (Score: {bench.single_score})",
            f"- **Multi-Core Throughput**: {bench.multi_ops_per_sec:,.0f} ops/sec (Score: {bench.multi_score})",
            f"- **Multi-Core Speedup Factor**: {bench.multi_thread_speedup:.2f}x",
            f"- **Memory Streaming Bandwidth**: {bench.mem_bandwidth_gbps:.2f} GB/s (Score: {bench.memory_score})",
            f"- **Benchmark Duration**: {bench.duration_seconds:.2f} seconds",
            f"",
        ])

    return "\n".join(lines)
