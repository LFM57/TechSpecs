"""Data models for scoring, tiers, and reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from techspecs.collectors import SpecSnapshot


@dataclass
class ComponentScores:
    cpu: float = 0.0
    gpu: float = 0.0
    memory: float = 0.0
    storage: float = 0.0


@dataclass
class WorkloadScores:
    office: float = 0.0
    gaming: float = 0.0
    development: float = 0.0
    ai_ml: float = 0.0


@dataclass
class RatingTier:
    tier_id: str
    name: str
    verdict: str  # "Very Weak", "Modest / Entry-Level", "Solid Mid-Range", "Powerful", "Very Powerful", "Apex Workstation"
    min_score: float
    max_score: float
    description: str
    badge_style: str  # rich style or color name


@dataclass
class BottleneckWarning:
    component: str  # "CPU", "GPU", "RAM", "Storage"
    severity: str  # "High", "Medium", "Low"
    description: str
    recommendation: str


@dataclass
class PowerReport:
    overall_score: float
    tier: RatingTier
    components: ComponentScores
    workloads: WorkloadScores
    bottlenecks: list[BottleneckWarning] = field(default_factory=list)
    spec: SpecSnapshot = field(default_factory=SpecSnapshot)
    benchmark_score: float | None = None
