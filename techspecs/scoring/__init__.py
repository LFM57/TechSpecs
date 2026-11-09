"""Scoring, baselines, and benchmark exports."""

from techspecs.scoring.baselines import (
    REFERENCE_BASELINES,
    BaselineComparison,
    BaselineProfile,
    compare_against_baselines,
)
from techspecs.scoring.benchmark import BenchmarkResult, run_quick_benchmark
from techspecs.scoring.engine import (
    TIERS,
    compute_cpu_score,
    compute_gpu_score,
    compute_memory_score,
    compute_overall_score,
    compute_storage_score,
    compute_workload_scores,
    detect_bottlenecks,
    evaluate_specs,
)
from techspecs.scoring.models import (
    BottleneckWarning,
    ComponentScores,
    PowerReport,
    RatingTier,
    WorkloadScores,
)

__all__ = [
    "BottleneckWarning",
    "ComponentScores",
    "WorkloadScores",
    "RatingTier",
    "PowerReport",
    "BaselineProfile",
    "BaselineComparison",
    "BenchmarkResult",
    "REFERENCE_BASELINES",
    "TIERS",
    "evaluate_specs",
    "compute_cpu_score",
    "compute_gpu_score",
    "compute_memory_score",
    "compute_storage_score",
    "compute_overall_score",
    "compute_workload_scores",
    "detect_bottlenecks",
    "compare_against_baselines",
    "run_quick_benchmark",
]
