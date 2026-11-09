"""Unit tests for the power scoring engine, tiers, and workloads."""

from __future__ import annotations

import unittest
from techspecs.collectors import (
    CPUInfo,
    GPUDevice,
    GPUInfo,
    MemoryInfo,
    SpecSnapshot,
    StorageDrive,
    StorageInfo,
    SystemInfo,
)
from techspecs.scoring import (
    ComponentScores,
    compute_cpu_score,
    compute_gpu_score,
    compute_memory_score,
    compute_overall_score,
    compute_storage_score,
    compute_workload_scores,
    detect_bottlenecks,
    evaluate_specs,
)


def _build_mock_spec(
    cpu_cores: int = 8,
    cpu_threads: int = 16,
    cpu_mhz: float = 4800.0,
    arch: str = "AMD Zen 4",
    gpu_name: str = "GeForce RTX 4070",
    is_igpu: bool = False,
    vram_mb: int = 12000,
    ram_gib: float = 32.0,
    disk_type: str = "NVMe SSD",
    is_nvme: bool = True,
    is_ssd: bool = True,
    disk_gib: float = 1000.0,
) -> SpecSnapshot:
    return SpecSnapshot(
        cpu=CPUInfo(
            model_name=f"Mock CPU ({arch})",
            vendor="MockVendor",
            architecture="x86_64",
            arch_family=arch,
            physical_cores=cpu_cores,
            logical_threads=cpu_threads,
            max_mhz=cpu_mhz,
            l3_cache_kb=32768,
            has_avx=True,
            has_avx2=True,
        ),
        gpu=GPUInfo(
            devices=[
                GPUDevice(
                    name=gpu_name,
                    vendor="NVIDIA" if "RTX" in gpu_name or "GTX" in gpu_name else "AMD",
                    is_integrated=is_igpu,
                    vram_mb=vram_mb,
                )
            ],
            primary_gpu=GPUDevice(
                name=gpu_name,
                vendor="NVIDIA" if "RTX" in gpu_name or "GTX" in gpu_name else "AMD",
                is_integrated=is_igpu,
                vram_mb=vram_mb,
            ),
            total_vram_mb=vram_mb,
            has_discrete_gpu=not is_igpu,
        ),
        memory=MemoryInfo(
            total_gib=ram_gib,
            available_gib=ram_gib * 0.7,
            used_gib=ram_gib * 0.3,
            has_zram=True,
        ),
        storage=StorageInfo(
            drives=[
                StorageDrive(
                    name="drive0",
                    model="Mock Drive",
                    media_type=disk_type,
                    is_ssd=is_ssd,
                    is_nvme=is_nvme,
                    size_gib=disk_gib,
                )
            ],
            primary_drive=StorageDrive(
                name="drive0",
                model="Mock Drive",
                media_type=disk_type,
                is_ssd=is_ssd,
                is_nvme=is_nvme,
                size_gib=disk_gib,
            ),
            total_disk_gib=disk_gib,
            has_nvme=is_nvme,
            has_ssd=is_ssd,
        ),
        system=SystemInfo(
            product_name="Mock PC",
            chassis_type="Desktop",
        ),
    )


class TestScoringEngine(unittest.TestCase):
    def test_ultra_budget_laptop_score(self):
        # Celeron 2C/2T, 4GB RAM, eMMC, UHD 600
        spec = _build_mock_spec(
            cpu_cores=2,
            cpu_threads=2,
            cpu_mhz=2600.0,
            arch="Intel Low-Power x86",
            gpu_name="Intel UHD Graphics 600",
            is_igpu=True,
            vram_mb=512,
            ram_gib=4.0,
            disk_type="eMMC Flash",
            is_nvme=False,
            is_ssd=True,
            disk_gib=64.0,
        )
        report = evaluate_specs(spec)
        self.assertLess(report.overall_score, 25.0)
        self.assertEqual(report.tier.verdict, "Very Weak")

    def test_entry_level_laptop_score(self):
        # Athlon 7120U 2C/2T, 6GB RAM, NVMe 128GB, Radeon 610M
        spec = _build_mock_spec(
            cpu_cores=2,
            cpu_threads=2,
            cpu_mhz=3550.0,
            arch="AMD Zen 2 (Mendocino)",
            gpu_name="Mendocino [Radeon 610M]",
            is_igpu=True,
            vram_mb=2048,
            ram_gib=5.6,
            disk_type="NVMe SSD",
            is_nvme=True,
            is_ssd=True,
            disk_gib=128.0,
        )
        report = evaluate_specs(spec)
        self.assertGreaterEqual(report.overall_score, 25.0)
        self.assertLess(report.overall_score, 45.0)
        self.assertEqual(report.tier.verdict, "Modest / Entry-Level")

    def test_high_end_gaming_score(self):
        # Ryzen 7 7800X3D, RTX 4070 Ti, 32GB RAM, 2TB NVMe
        spec = _build_mock_spec(
            cpu_cores=8,
            cpu_threads=16,
            cpu_mhz=5050.0,
            arch="AMD Zen 4",
            gpu_name="GeForce RTX 4070 Ti",
            is_igpu=False,
            vram_mb=12000,
            ram_gib=32.0,
            disk_type="NVMe SSD",
            is_nvme=True,
            is_ssd=True,
            disk_gib=2000.0,
        )
        report = evaluate_specs(spec)
        self.assertGreaterEqual(report.overall_score, 80.0)
        self.assertIn(report.tier.verdict, ("Very Powerful", "Powerful"))

    def test_bottleneck_detection(self):
        # High CPU and GPU, but crippled by 4GB RAM
        spec = _build_mock_spec(
            cpu_cores=8,
            cpu_threads=16,
            gpu_name="GeForce RTX 4070",
            is_igpu=False,
            ram_gib=4.0,
        )
        report = evaluate_specs(spec)
        bottleneck_components = [b.component for b in report.bottlenecks]
        self.assertIn("Memory (RAM)", bottleneck_components)

    def test_workload_scores(self):
        spec = _build_mock_spec()
        report = evaluate_specs(spec)
        self.assertGreater(report.workloads.office, 0)
        self.assertGreater(report.workloads.gaming, 0)
        self.assertGreater(report.workloads.development, 0)
        self.assertGreater(report.workloads.ai_ml, 0)


if __name__ == "__main__":
    unittest.main()
