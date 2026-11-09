"""GPU hardware spec collector."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GPUDevice:
    name: str = "Unknown GPU"
    vendor: str = "Unknown"
    is_integrated: bool = True
    vram_mb: int | None = None
    vram_type: str = "Unknown"
    pci_id: str | None = None
    driver: str | None = None
    driver_version: str | None = None


@dataclass
class GPUInfo:
    devices: list[GPUDevice] = field(default_factory=list)
    primary_gpu: GPUDevice | None = None
    total_vram_mb: int = 0
    has_discrete_gpu: bool = False


_INTEGRATED_KEYWORDS = [
    "radeon 610m",
    "radeon 660m",
    "radeon 680m",
    "radeon 740m",
    "radeon 760m",
    "radeon 780m",
    "radeon 880m",
    "radeon 890m",
    "radeon vega",
    "iris xe",
    "iris plus",
    "iris pro",
    "uhd graphics",
    "hd graphics",
    "intel arc graphics",  # mobile core ultra iGPU
    "mendocino",
    "raphael",
    "integrated",
    "renoir",
    "cezanne",
    "barcelo",
    "rembrandt",
    "phoenix",
    "hawk point",
    "strix point",
]


def _is_integrated_gpu(device_name: str, vendor: str) -> bool:
    """Classify if GPU is an integrated graphics processor (iGPU)."""
    lower = device_name.lower()
    for kw in _INTEGRATED_KEYWORDS:
        if kw in lower:
            return True
    if "intel" in vendor.lower() and not ("arc a" in lower or "arc b" in lower or "arc pro" in lower):
        return True
    return False


def _parse_lspci_vmm() -> list[dict[str, str]]:
    """Parse lspci -vmm output for display/graphics adapters."""
    devices = []
    try:
        res = subprocess.run(["lspci", "-vmm"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            blocks = res.stdout.strip().split("\n\n")
            for block in blocks:
                d = {}
                for line in block.split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        d[k.strip()] = v.strip()
                cls = d.get("Class", "")
                if any(x in cls for x in ("VGA", "3D", "Display")):
                    devices.append(d)
    except Exception:
        pass
    return devices


def _read_amd_vram(card_path: Path) -> int | None:
    """Read AMD VRAM total from sysfs."""
    vram_file = card_path / "device" / "mem_info_vram_total"
    if vram_file.is_file():
        try:
            bytes_val = int(vram_file.read_text().strip())
            return int(bytes_val / (1024 * 1024))
        except Exception:
            pass
    return None


def _check_nvidia_smi() -> list[dict[str, str | int]]:
    """Query nvidia-smi if installed."""
    results = []
    try:
        cmd = ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        if res.returncode == 0:
            for line in res.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    name, vram_str, driver = parts[0], parts[1], parts[2]
                    vram_mb = int(vram_str) if vram_str.isdigit() else None
                    results.append({"name": name, "vram_mb": vram_mb, "driver_version": driver})
    except Exception:
        pass
    return results


def collect_gpu_info() -> GPUInfo:
    """Collect comprehensive GPU specs from lspci, sysfs, and driver utilities."""
    gpu_info = GPUInfo()
    discovered_devices: list[GPUDevice] = []

    # 1. Inspect lspci devices
    lspci_entries = _parse_lspci_vmm()
    for entry in lspci_entries:
        dev_name = entry.get("Device", "Unknown Graphics Adapter")
        vendor = entry.get("Vendor", "Unknown Vendor")
        slot = entry.get("Slot")
        is_igpu = _is_integrated_gpu(dev_name, vendor)

        # Check sysfs for DRM info corresponding to this PCI device
        vram_mb = None
        driver_name = None
        driver_version = None

        drm_dir = Path("/sys/class/drm")
        if drm_dir.is_dir():
            for card in drm_dir.glob("card*"):
                if "-" in card.name:
                    continue  # skip connector symlinks like card1-eDP-1
                try:
                    target = card.resolve()
                    if slot and slot in str(target):
                        vram = _read_amd_vram(card)
                        if vram:
                            vram_mb = vram
                        driver_symlink = card / "device" / "driver"
                        if driver_symlink.is_symlink():
                            driver_name = driver_symlink.resolve().name
                            ver_file = driver_symlink / "module" / "version"
                            if ver_file.is_file():
                                driver_version = ver_file.read_text().strip()
                except Exception:
                    continue

        device = GPUDevice(
            name=dev_name,
            vendor=vendor,
            is_integrated=is_igpu,
            vram_mb=vram_mb,
            vram_type="Shared / Dynamic" if is_igpu else "Dedicated VRAM",
            pci_id=slot,
            driver=driver_name,
            driver_version=driver_version,
        )
        discovered_devices.append(device)

    # 2. Check nvidia-smi for dedicated NVIDIA GPUs
    nvidia_gpus = _check_nvidia_smi()
    for nv in nvidia_gpus:
        matched = False
        for dev in discovered_devices:
            if "nvidia" in dev.vendor.lower() or "nvidia" in dev.name.lower():
                dev.name = str(nv["name"])
                dev.vendor = "NVIDIA"
                dev.is_integrated = False
                dev.vram_mb = int(nv["vram_mb"]) if nv["vram_mb"] else dev.vram_mb
                dev.vram_type = "Dedicated GDDR"
                dev.driver = "nvidia"
                dev.driver_version = str(nv["driver_version"])
                matched = True
                break
        if not matched:
            discovered_devices.append(
                GPUDevice(
                    name=str(nv["name"]),
                    vendor="NVIDIA",
                    is_integrated=False,
                    vram_mb=int(nv["vram_mb"]) if nv["vram_mb"] else None,
                    vram_type="Dedicated GDDR",
                    driver="nvidia",
                    driver_version=str(nv["driver_version"]),
                )
            )

    # Fallback if no devices detected (e.g. container / VM without direct PCI pass)
    if not discovered_devices:
        discovered_devices.append(
            GPUDevice(
                name="Generic / Virtual GPU",
                vendor="Generic",
                is_integrated=True,
                vram_mb=512,
                vram_type="Virtual",
            )
        )

    gpu_info.devices = discovered_devices
    gpu_info.has_discrete_gpu = any(not d.is_integrated for d in discovered_devices)

    # Select primary GPU: prefer discrete if available, else first integrated
    discrete_list = [d for d in discovered_devices if not d.is_integrated]
    if discrete_list:
        gpu_info.primary_gpu = discrete_list[0]
    else:
        gpu_info.primary_gpu = discovered_devices[0]

    gpu_info.total_vram_mb = sum(d.vram_mb or 0 for d in discovered_devices)

    return gpu_info
