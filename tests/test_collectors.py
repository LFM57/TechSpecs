"""Unit tests for hardware spec collectors."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from techspecs.collectors import SpecSnapshot, collect_specs
from techspecs.collectors.cpu import (
    CPUInfo,
    _collect_sysfs_cache,
    _detect_arch_family,
    _parse_cache_size,
    collect_cpu_info,
)
from techspecs.collectors.gpu import _is_integrated_gpu, _parse_lspci_vmm, collect_gpu_info
from techspecs.collectors.memory import collect_memory_info
from techspecs.collectors.storage import _classify_media, collect_storage_info
from techspecs.collectors.system import collect_system_info


class TestCPUCollector(unittest.TestCase):
    def test_parse_cache_size(self):
        self.assertEqual(_parse_cache_size("512K"), 512)
        self.assertEqual(_parse_cache_size("2M"), 2048)
        self.assertEqual(_parse_cache_size("64 KiB"), 64)
        self.assertEqual(_parse_cache_size("16 MiB"), 16384)
        self.assertEqual(_parse_cache_size("invalid"), 0)

    def test_detect_arch_family(self):
        self.assertIn("Zen 2", _detect_arch_family("AMD Athlon Silver 7120U with Radeon Graphics", "AuthenticAMD"))
        self.assertIn("Zen 4", _detect_arch_family("AMD Ryzen 7 7800X3D", "AuthenticAMD"))
        self.assertIn("Zen 5", _detect_arch_family("AMD Ryzen 9 9950X", "AuthenticAMD"))
        self.assertIn("Raptor Lake", _detect_arch_family("Intel Core i7-13700K", "GenuineIntel"))
        self.assertIn("Alder Lake", _detect_arch_family("Intel Core i5-12400F", "GenuineIntel"))
        self.assertIn("Low-Power", _detect_arch_family("Intel Celeron N4020", "GenuineIntel"))

    def test_live_cpu_collection(self):
        cpu = collect_cpu_info()
        self.assertIsInstance(cpu, CPUInfo)
        self.assertGreater(cpu.logical_threads, 0)
        self.assertGreater(cpu.physical_cores, 0)
        self.assertTrue(len(cpu.model_name) > 0)


class TestGPUCollector(unittest.TestCase):
    def test_is_integrated(self):
        self.assertTrue(_is_integrated_gpu("Mendocino [Radeon 610M]", "AMD"))
        self.assertTrue(_is_integrated_gpu("Intel Iris Xe Graphics", "Intel"))
        self.assertTrue(_is_integrated_gpu("Intel UHD Graphics 630", "Intel"))
        self.assertFalse(_is_integrated_gpu("GeForce RTX 4070 Ti SUPER", "NVIDIA"))
        self.assertFalse(_is_integrated_gpu("Radeon RX 7900 XTX", "AMD"))

    def test_live_gpu_collection(self):
        gpu_info = collect_gpu_info()
        self.assertIsNotNone(gpu_info.primary_gpu)
        self.assertTrue(len(gpu_info.devices) >= 1)


class TestMemoryCollector(unittest.TestCase):
    def test_live_memory_collection(self):
        mem = collect_memory_info()
        self.assertGreater(mem.total_gib, 0.5)
        self.assertGreater(mem.available_gib, 0.0)
        self.assertLessEqual(mem.usage_percent, 100.0)


class TestStorageCollector(unittest.TestCase):
    def test_classify_media(self):
        media, is_ssd, is_nvme = _classify_media("nvme0n1", "nvme", False, "Samsung 980 PRO")
        self.assertEqual(media, "NVMe SSD")
        self.assertTrue(is_ssd)
        self.assertTrue(is_nvme)

        media, is_ssd, is_nvme = _classify_media("sda", "sata", False, "Crucial MX500")
        self.assertIn("SSD", media)
        self.assertTrue(is_ssd)
        self.assertFalse(is_nvme)

        media, is_ssd, is_nvme = _classify_media("sdb", "sata", True, "WDC WD10EZEX")
        self.assertIn("HDD", media)
        self.assertFalse(is_ssd)
        self.assertFalse(is_nvme)

    def test_live_storage_collection(self):
        storage = collect_storage_info()
        self.assertGreater(len(storage.drives), 0)
        self.assertGreater(storage.total_disk_gib, 0.0)


class TestSystemCollector(unittest.TestCase):
    def test_live_system_collection(self):
        sys_info = collect_system_info()
        self.assertTrue(len(sys_info.os_name) > 0)
        self.assertTrue(len(sys_info.architecture) > 0)


class TestAggregateCollector(unittest.TestCase):
    def test_collect_specs(self):
        snapshot = collect_specs()
        self.assertIsInstance(snapshot, SpecSnapshot)
        self.assertTrue(snapshot.collected_at)
        self.assertIsNotNone(snapshot.cpu)
        self.assertIsNotNone(snapshot.gpu)
        self.assertIsNotNone(snapshot.memory)
        self.assertIsNotNone(snapshot.storage)
        self.assertIsNotNone(snapshot.system)


if __name__ == "__main__":
    unittest.main()
