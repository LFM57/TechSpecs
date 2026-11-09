"""CPU hardware spec collector."""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CPUInfo:
    model_name: str = "Unknown CPU"
    vendor: str = "Unknown"
    architecture: str = ""
    arch_family: str = "Unknown"
    physical_cores: int = 1
    logical_threads: int = 1
    sockets: int = 1
    base_mhz: float | None = None
    max_mhz: float | None = None
    current_mhz: float | None = None
    l1_cache_kb: int = 0
    l2_cache_kb: int = 0
    l3_cache_kb: int = 0
    flags: list[str] = field(default_factory=list)
    has_avx: bool = False
    has_avx2: bool = False
    has_avx512: bool = False
    has_fma: bool = False
    has_aes: bool = False
    bogomips: float | None = None


def _detect_arch_family(model_name: str, vendor: str, family: int = 0, model: int = 0) -> str:
    """Infer microarchitecture family from model name, family, and model ids."""
    lower = model_name.lower()

    if "amd" in vendor.lower() or "amd" in lower:
        # Match Mendocino / Zen 2 / Zen 3 / Zen 4 / Zen 5
        if "7120u" in lower or "7220u" in lower or "mendocino" in lower:
            return "AMD Zen 2 (Mendocino)"
        if re.search(r"ryzen\s+[3579]\s+9\d{3}", lower):
            return "AMD Zen 5"
        if re.search(r"ryzen\s+[3579]\s+[78]\d{3}", lower):
            return "AMD Zen 4"
        if re.search(r"ryzen\s+[3579]\s+[56]\d{3}", lower):
            return "AMD Zen 3"
        if re.search(r"ryzen\s+[3579]\s+[34]\d{3}", lower):
            return "AMD Zen 2"
        if re.search(r"ryzen\s+[3579]\s+[12]\d{3}", lower):
            return "AMD Zen / Zen+"
        if family == 23 or family == 25:
            return "AMD Zen"
        return "AMD x86_64"

    if "intel" in vendor.lower() or "intel" in lower:
        if re.search(r"(ultra\s+[579]\s+\d{3}|core\s+i[3579]-1[45]\d{2})", lower):
            return "Intel Raptor Lake / Arrow Lake"
        if re.search(r"core\s+i[3579]-13\d{2}", lower):
            return "Intel Raptor Lake (13th Gen)"
        if re.search(r"core\s+i[3579]-12\d{2}", lower):
            return "Intel Alder Lake (12th Gen)"
        if re.search(r"core\s+i[3579]-1[01]\d{2}", lower):
            return "Intel Tiger Lake / Ice Lake"
        if re.search(r"core\s+i[3579]-[6789]\d{2}", lower):
            return "Intel Skylake / Comet Lake"
        if "celeron" in lower or "pentium" in lower:
            return "Intel Low-Power x86"
        return "Intel Core"

    if "apple" in lower or "m1" in lower or "m2" in lower or "m3" in lower or "m4" in lower:
        return "Apple Silicon ARM"

    return platform.machine() or "Unknown Architecture"


def _read_sysfs_freq(path: str) -> float | None:
    """Read frequency from sysfs in kHz and return MHz."""
    try:
        val = Path(path).read_text().strip()
        if val.isdigit():
            return round(int(val) / 1000.0, 1)
    except Exception:
        pass
    return None


def _parse_cache_size(size_str: str) -> int:
    """Parse cache size string like '512K', '2M', '64 KiB' into KB."""
    match = re.search(r"(\d+(?:\.\d+)?)\s*([KkMmGg])", size_str)
    if not match:
        return 0
    val, unit = float(match.group(1)), match.group(2).upper()
    if unit == "K":
        return int(val)
    if unit == "M":
        return int(val * 1024)
    if unit == "G":
        return int(val * 1024 * 1024)
    return int(val)


def _collect_sysfs_cache() -> tuple[int, int, int]:
    """Inspect /sys/devices/system/cpu/cpu0/cache/ and return (L1_KB, L2_KB, L3_KB)."""
    l1_kb = 0
    l2_kb = 0
    l3_kb = 0

    cache_dir = Path("/sys/devices/system/cpu/cpu0/cache")
    if cache_dir.is_dir():
        for idx in cache_dir.glob("index*"):
            try:
                lvl = (idx / "level").read_text().strip()
                sz_str = (idx / "size").read_text().strip()
                sz_kb = _parse_cache_size(sz_str)
                if lvl == "1":
                    l1_kb += sz_kb
                elif lvl == "2":
                    l2_kb += sz_kb
                elif lvl == "3":
                    l3_kb += sz_kb
            except Exception:
                continue

    return l1_kb, l2_kb, l3_kb


def _collect_from_lscpu() -> dict:
    """Collect supplemental info via lscpu --json if available."""
    try:
        res = subprocess.run(["lscpu", "--json"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            result = {}

            def traverse(items):
                for item in items:
                    field_name = item.get("field", "").rstrip(":")
                    field_data = item.get("data")
                    if field_name and field_data is not None:
                        result[field_name] = field_data
                    if "children" in item:
                        traverse(item["children"])

            if "lscpu" in data:
                traverse(data["lscpu"])
            return result
    except Exception:
        pass
    return {}


def collect_cpu_info() -> CPUInfo:
    """Collect comprehensive CPU information from system interfaces."""
    info = CPUInfo()
    info.architecture = platform.machine()

    cpuinfo_path = Path("/proc/cpuinfo")
    logical_cores = 0
    core_ids: set[int] = set()
    physical_ids: set[int] = set()
    family = 0
    model = 0
    mhz_list: list[float] = []

    if cpuinfo_path.is_file():
        try:
            content = cpuinfo_path.read_text(errors="replace")
            blocks = content.strip().split("\n\n")
            for block in blocks:
                lines = block.split("\n")
                b_dict = {}
                for line in lines:
                    if ":" in line:
                        k, v = line.split(":", 1)
                        b_dict[k.strip()] = v.strip()

                if "processor" in b_dict:
                    logical_cores += 1

                if not info.model_name or info.model_name == "Unknown CPU":
                    if "model name" in b_dict:
                        info.model_name = b_dict["model name"]
                if not info.vendor or info.vendor == "Unknown":
                    if "vendor_id" in b_dict:
                        info.vendor = b_dict["vendor_id"]

                if "cpu family" in b_dict and b_dict["cpu family"].isdigit():
                    family = int(b_dict["cpu family"])
                if "model" in b_dict and b_dict["model"].isdigit():
                    model = int(b_dict["model"])

                if "core id" in b_dict and b_dict["core id"].isdigit():
                    core_ids.add(int(b_dict["core id"]))
                if "physical id" in b_dict and b_dict["physical id"].isdigit():
                    physical_ids.add(int(b_dict["physical id"]))

                if "cpu MHz" in b_dict:
                    try:
                        mhz_list.append(float(b_dict["cpu MHz"]))
                    except ValueError:
                        pass

                if not info.flags and "flags" in b_dict:
                    info.flags = b_dict["flags"].split()

                if info.bogomips is None and "bogomips" in b_dict:
                    try:
                        info.bogomips = float(b_dict["bogomips"])
                    except ValueError:
                        pass
        except Exception:
            pass

    info.logical_threads = logical_cores or os.cpu_count() or 1
    info.physical_cores = len(core_ids) if core_ids else info.logical_threads
    info.sockets = len(physical_ids) if physical_ids else 1

    if mhz_list:
        info.current_mhz = round(sum(mhz_list) / len(mhz_list), 1)

    # Max / Min frequencies from sysfs
    max_mhz = _read_sysfs_freq("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq")
    if max_mhz is None:
        max_mhz = _read_sysfs_freq("/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq")
    info.max_mhz = max_mhz

    min_mhz = _read_sysfs_freq("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq")
    if min_mhz is None:
        min_mhz = _read_sysfs_freq("/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq")
    info.base_mhz = min_mhz

    # Cache info from sysfs
    l1, l2, l3 = _collect_sysfs_cache()
    info.l1_cache_kb = l1
    info.l2_cache_kb = l2
    info.l3_cache_kb = l3

    # Fallback to lscpu if needed
    lscpu_data = _collect_from_lscpu()
    if lscpu_data:
        if info.model_name in ("Unknown CPU", "") and "Model name" in lscpu_data:
            info.model_name = lscpu_data["Model name"]
        if info.vendor in ("Unknown", "") and "Vendor ID" in lscpu_data:
            info.vendor = lscpu_data["Vendor ID"]
        if not info.max_mhz and "CPU max MHz" in lscpu_data:
            try:
                info.max_mhz = round(float(lscpu_data["CPU max MHz"]), 1)
            except ValueError:
                pass
        if not info.l3_cache_kb and "L3" in lscpu_data:
            info.l3_cache_kb = _parse_cache_size(lscpu_data["L3"])
        if not info.l2_cache_kb and "L2" in lscpu_data:
            info.l2_cache_kb = _parse_cache_size(lscpu_data["L2"])
        if not info.flags and "Flags" in lscpu_data:
            info.flags = lscpu_data["Flags"].split()

    # Feature flags
    flags_set = set(info.flags)
    info.has_avx = "avx" in flags_set
    info.has_avx2 = "avx2" in flags_set
    info.has_avx512 = any(f.startswith("avx512") for f in flags_set)
    info.has_fma = "fma" in flags_set
    info.has_aes = "aes" in flags_set

    # Microarchitecture detection
    info.arch_family = _detect_arch_family(info.model_name, info.vendor, family, model)

    return info
