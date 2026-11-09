"""Terminal dashboard reporter using Rich with plain ANSI fallback."""

from __future__ import annotations

import sys
from techspecs.scoring import BenchmarkResult, PowerReport, compare_against_baselines

try:
    from rich.box import ROUNDED, SIMPLE
    from rich.columns import Columns
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def _make_bar(score: float, width: int = 20) -> str:
    """Generate a Unicode block progress bar."""
    clamped = max(0.0, min(100.0, score))
    filled = int(round((clamped / 100.0) * width))
    empty = width - filled
    return "█" * filled + "░" * empty


def _score_color(score: float) -> str:
    """Return styling color based on score magnitude."""
    if score >= 80.0:
        return "bold magenta"
    if score >= 65.0:
        return "bold green"
    if score >= 45.0:
        return "bold cyan"
    if score >= 25.0:
        return "bold yellow"
    return "bold red"


def render_rich_dashboard(report: PowerReport, bench: BenchmarkResult | None = None) -> None:
    """Render comprehensive terminal dashboard using Rich."""
    console = Console()
    spec = report.spec
    comps = report.components
    work = report.workloads
    tier = report.tier

    # 1. Header & System Overview
    sys_title = f"[bold cyan]TechSpecs[/bold cyan] [dim]• Hardware Spec Analyzer & Power Rating[/dim]"
    sys_info_text = (
        f"[bold]{spec.system.manufacturer} {spec.system.product_name}[/bold] ({spec.system.chassis_type})\n"
        f"OS: [cyan]{spec.system.os_name} {spec.system.os_version}[/cyan]  •  Kernel: [dim]{spec.system.kernel}[/dim]\n"
        f"Architecture: [yellow]{spec.cpu.architecture}[/yellow]  •  Family: [yellow]{spec.cpu.arch_family}[/yellow]"
    )
    if spec.system.has_battery:
        bat_str = f"{spec.system.battery_charge_pct:.0f}%" if spec.system.battery_charge_pct else "N/A"
        health_str = f"{spec.system.battery_health_pct:.1f}%" if spec.system.battery_health_pct else "N/A"
        sys_info_text += f"\nBattery: [green]{bat_str}[/green] charge  •  Health: [green]{health_str}[/green]"

    console.print(Panel(sys_info_text, title=sys_title, box=ROUNDED, border_style="cyan"))

    # 2. Main Verdict Banner
    overall_color = _score_color(report.overall_score)
    verdict_text = Text()
    verdict_text.append(f"  POWER SCORE: ", style="bold white")
    verdict_text.append(f"{report.overall_score:.1f} / 100", style=f"{overall_color} underline")
    verdict_text.append(f"   ►  VERDICT: ", style="bold white")
    verdict_text.append(f"[{tier.verdict.upper()}]", style=tier.badge_style)
    verdict_text.append(f"\n  Category: {tier.name} — {tier.description}", style="dim italic")

    console.print(Panel(verdict_text, box=ROUNDED, border_style=tier.badge_style))

    # 3. Component Breakdown Table
    comp_table = Table(title="Component Specifications & Sub-Scores", box=ROUNDED, expand=True)
    comp_table.add_column("Subsystem", style="bold cyan", width=14)
    comp_table.add_column("Specs", style="white")
    comp_table.add_column("Score (0-100)", justify="right", width=14)
    comp_table.add_column("Gauge", justify="left", width=24)

    # CPU row
    cpu_detail = f"{spec.cpu.model_name} ({spec.cpu.physical_cores}C / {spec.cpu.logical_threads}T"
    if spec.cpu.max_mhz:
        cpu_detail += f" @ {spec.cpu.max_mhz:.0f} MHz"
    if spec.cpu.l3_cache_kb:
        cpu_detail += f", {spec.cpu.l3_cache_kb // 1024}MB L3"
    cpu_detail += ")"
    cpu_col = _score_color(comps.cpu)
    comp_table.add_row(
        "CPU",
        cpu_detail,
        f"[{cpu_col}]{comps.cpu:.1f}[/{cpu_col}]",
        f"[{cpu_col}]{_make_bar(comps.cpu)}[/{cpu_col}]",
    )

    # GPU row
    primary_gpu = spec.gpu.primary_gpu
    gpu_detail = primary_gpu.name if primary_gpu else "Unknown GPU"
    if primary_gpu:
        gpu_type = "iGPU" if primary_gpu.is_integrated else "dGPU"
        gpu_detail += f" ({gpu_type}"
        if primary_gpu.vram_mb:
            gpu_detail += f", {primary_gpu.vram_mb} MB"
        gpu_detail += ")"
    gpu_col = _score_color(comps.gpu)
    comp_table.add_row(
        "GPU",
        gpu_detail,
        f"[{gpu_col}]{comps.gpu:.1f}[/{gpu_col}]",
        f"[{gpu_col}]{_make_bar(comps.gpu)}[/{gpu_col}]",
    )

    # RAM row
    ram_detail = f"{spec.memory.total_gib:.1f} GiB Total (Swap: {spec.memory.swap_total_gib:.1f} GiB"
    if spec.memory.has_zram:
        ram_detail += ", ZRAM enabled"
    ram_detail += ")"
    ram_col = _score_color(comps.memory)
    comp_table.add_row(
        "Memory (RAM)",
        ram_detail,
        f"[{ram_col}]{comps.memory:.1f}[/{ram_col}]",
        f"[{ram_col}]{_make_bar(comps.memory)}[/{ram_col}]",
    )

    # Storage row
    primary_disk = spec.storage.primary_drive
    disk_detail = f"{primary_disk.media_type if primary_disk else 'Drive'} • {spec.storage.total_disk_gib:.1f} GiB"
    if primary_disk and primary_disk.model:
        disk_detail += f" ({primary_disk.model.strip()})"
    disk_col = _score_color(comps.storage)
    comp_table.add_row(
        "Storage",
        disk_detail,
        f"[{disk_col}]{comps.storage:.1f}[/{disk_col}]",
        f"[{disk_col}]{_make_bar(comps.storage)}[/{disk_col}]",
    )

    console.print(comp_table)

    # 4. Workload Ratings Table
    work_table = Table(title="Real-World Workload Suitability", box=ROUNDED, expand=True)
    work_table.add_column("Workload Profile", style="bold yellow", width=22)
    work_table.add_column("Rating", justify="right", width=12)
    work_table.add_column("Gauge", justify="left", width=22)
    work_table.add_column("Experience Assessment", style="white")

    def _assess(val: float, high_t: str, mid_t: str, low_t: str) -> str:
        if val >= 65:
            return f"[green]{high_t}[/green]"
        if val >= 38:
            return f"[yellow]{mid_t}[/yellow]"
        return f"[dim red]{low_t}[/dim red]"

    work_table.add_row(
        "Daily Office / Web",
        f"[{_score_color(work.office)}]{work.office:.1f}[/{_score_color(work.office)}]",
        f"[{_score_color(work.office)}]{_make_bar(work.office)}[/{_score_color(work.office)}]",
        _assess(work.office, "Smooth multi-tab web, docs & 1080p video", "Good for standard daily productivity", "Sluggish under heavy web multitasking"),
    )
    work_table.add_row(
        "3D Gaming & Graphics",
        f"[{_score_color(work.gaming)}]{work.gaming:.1f}[/{_score_color(work.gaming)}]",
        f"[{_score_color(work.gaming)}]{_make_bar(work.gaming)}[/{_score_color(work.gaming)}]",
        _assess(work.gaming, "High-FPS 1440p / 4K gaming ready", "1080p esports / lightweight 3D / indie games", "Only 2D / retro indie gaming possible"),
    )
    work_table.add_row(
        "Software Engineering",
        f"[{_score_color(work.development)}]{work.development:.1f}[/{_score_color(work.development)}]",
        f"[{_score_color(work.development)}]{_make_bar(work.development)}[/{_score_color(work.development)}]",
        _assess(work.development, "Fast compilation, Docker & local virtualization", "Solid web & script development", "Basic code editing; compile times slow"),
    )
    work_table.add_row(
        "AI & Machine Learning",
        f"[{_score_color(work.ai_ml)}]{work.ai_ml:.1f}[/{_score_color(work.ai_ml)}]",
        f"[{_score_color(work.ai_ml)}]{_make_bar(work.ai_ml)}[/{_score_color(work.ai_ml)}]",
        _assess(work.ai_ml, "Local high-parameter LLM inference & training", "Small quantized model execution", "Cloud/remote API inference recommended"),
    )

    console.print(work_table)

    # 5. Baseline Comparison Chart
    base_table = Table(title="Standard Baseline Comparisons (Where Your PC Lands)", box=ROUNDED, expand=True)
    base_table.add_column("Tier / Baseline", style="bold", width=32)
    base_table.add_column("Score", justify="right", width=8)
    base_table.add_column("Comparative Spectrum", justify="left", width=24)
    base_table.add_column("Relative Delta", style="white")

    baselines = compare_against_baselines(report.overall_score)
    inserted_current = False

    for b in baselines:
        if not inserted_current and report.overall_score <= b.baseline_score:
            # Insert current computer here
            base_table.add_row(
                f"[bold green]► YOUR PC ({spec.system.product_name})[/bold green]",
                f"[bold green]{report.overall_score:.1f}[/bold green]",
                f"[bold green]{_make_bar(report.overall_score)}[/bold green]",
                f"[bold green]◄ CURRENT SYSTEM ({tier.verdict})[/bold green]",
            )
            inserted_current = True

        b_color = _score_color(b.baseline_score)
        base_table.add_row(
            f"{b.name}",
            f"[{b_color}]{b.baseline_score:.1f}[/{b_color}]",
            f"[{b_color}]{_make_bar(b.baseline_score)}[/{b_color}]",
            f"{b.summary}",
        )

    if not inserted_current:
        # Highest tier
        base_table.add_row(
            f"[bold green]► YOUR PC ({spec.system.product_name})[/bold green]",
            f"[bold green]{report.overall_score:.1f}[/bold green]",
            f"[bold green]{_make_bar(report.overall_score)}[/bold green]",
            f"[bold green]◄ CURRENT SYSTEM ({tier.verdict})[/bold green]",
        )

    console.print(base_table)

    # 6. Bottleneck Warnings
    if report.bottlenecks:
        bot_text = Text()
        for i, bn in enumerate(report.bottlenecks):
            color = "red" if bn.severity == "High" else "yellow"
            bot_text.append(f"• [{bn.severity.upper()} IMPACT] {bn.component}: ", style=f"bold {color}")
            bot_text.append(f"{bn.description}\n", style="white")
            bot_text.append(f"  Advice: {bn.recommendation}\n\n", style="dim cyan")
        console.print(Panel(bot_text, title="Hardware Bottleneck Alerts & Recommendations", box=ROUNDED, border_style="yellow"))

    # 7. Benchmark Results Panel (if available)
    if bench:
        bench_text = (
            f"[bold]Empirical Micro-Benchmark Score:[/bold] [{_score_color(bench.overall_benchmark_score)}]{bench.overall_benchmark_score:.1f} / 100[/{_score_color(bench.overall_benchmark_score)}]\n"
            f"• Single-Core Speed: [cyan]{bench.single_ops_per_sec:,.0f} ops/sec[/cyan] (Score: {bench.single_score:.1f})\n"
            f"• Multi-Core Speed:  [cyan]{bench.multi_ops_per_sec:,.0f} ops/sec[/cyan] (Score: {bench.multi_score:.1f}) — Multi-thread speedup: [green]{bench.multi_thread_speedup:.2f}x[/green]\n"
            f"• Memory Bandwidth:  [cyan]{bench.mem_bandwidth_gbps:.2f} GB/s[/cyan] (Score: {bench.memory_score:.1f})\n"
            f"• Total Duration:    [dim]{bench.duration_seconds:.2f} seconds[/dim]"
        )
        console.print(Panel(bench_text, title="Micro-Benchmark Empirical Calibration", box=ROUNDED, border_style="green"))


def render_ansi_fallback(report: PowerReport, bench: BenchmarkResult | None = None) -> None:
    """Fallback plain text renderer for non-rich environments."""
    spec = report.spec
    comps = report.components
    tier = report.tier

    print("=" * 72)
    print(f" TECHSPECS: HARDWARE SPEC ANALYZER & POWER RATING")
    print(f" System: {spec.system.manufacturer} {spec.system.product_name} ({spec.system.chassis_type})")
    print(f" OS: {spec.system.os_name} | Kernel: {spec.system.kernel}")
    print("=" * 72)
    print(f" OVERALL POWER SCORE: {report.overall_score:.1f} / 100")
    print(f" VERDICT: {tier.verdict.upper()} ({tier.name})")
    print(f" Description: {tier.description}")
    print("-" * 72)
    print(" COMPONENT BREAKDOWN:")
    print(f"  CPU:     {comps.cpu:5.1f}/100 | {_make_bar(comps.cpu)} | {spec.cpu.model_name}")
    print(f"  GPU:     {comps.gpu:5.1f}/100 | {_make_bar(comps.gpu)} | {spec.gpu.primary_gpu.name if spec.gpu.primary_gpu else 'None'}")
    print(f"  RAM:     {comps.memory:5.1f}/100 | {_make_bar(comps.memory)} | {spec.memory.total_gib:.1f} GiB")
    print(f"  Storage: {comps.storage:5.1f}/100 | {_make_bar(comps.storage)} | {spec.storage.total_disk_gib:.1f} GiB")
    print("-" * 72)
    print(" BASELINE COMPARISONS:")
    for b in compare_against_baselines(report.overall_score):
        print(f"  {b.name:<32} {b.baseline_score:5.1f} | {_make_bar(b.baseline_score)} | {b.summary}")
    print("=" * 72)


def render_dashboard(report: PowerReport, bench: BenchmarkResult | None = None) -> None:
    """Render terminal output using Rich if available, else plain ANSI."""
    if HAS_RICH and sys.stdout.isatty():
        render_rich_dashboard(report, bench)
    elif HAS_RICH:
        # Non-tty but rich is available
        render_rich_dashboard(report, bench)
    else:
        render_ansi_fallback(report, bench)
