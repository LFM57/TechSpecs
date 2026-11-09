"""Storage and drive spec collector."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StorageDrive:
    name: str = ""
    model: str = "Unknown Drive"
    size_bytes: int = 0
    size_gib: float = 0.0
    media_type: str = "Unknown"  # NVMe SSD, SATA SSD, HDD, eMMC
    is_ssd: bool = True
    is_nvme: bool = False
    transport: str | None = None
    mountpoint: str | None = None


@dataclass
class StorageInfo:
    drives: list[StorageDrive] = field(default_factory=list)
    primary_drive: StorageDrive | None = None
    total_disk_gib: float = 0.0
    root_total_gib: float = 0.0
    root_free_gib: float = 0.0
    root_used_gib: float = 0.0
    root_used_percent: float = 0.0
    has_nvme: bool = False
    has_ssd: bool = False


def _classify_media(name: str, tran: str | None, rota: bool | None, model: str) -> tuple[str, bool, bool]:
    """Classify drive media type, is_ssd, is_nvme."""
    lower_model = (model or "").lower()
    lower_tran = (tran or "").lower()

    if lower_tran == "nvme" or "nvme" in name.lower() or "nvme" in lower_model:
        return "NVMe SSD", True, True

    if lower_tran == "mmc" or "mmcblk" in name.lower() or "emmc" in lower_model:
        return "eMMC Flash", True, False

    if rota is False or "ssd" in lower_model:
        if lower_tran == "sata" or "sata" in lower_model:
            return "SATA SSD", True, False
        return "Solid State Drive (SSD)", True, False

    if rota is True:
        return "Rotational Hard Drive (HDD)", False, False

    return "Storage Drive", True, False


def collect_storage_info() -> StorageInfo:
    """Collect storage specifications using lsblk and sysfs."""
    info = StorageInfo()
    drives: list[StorageDrive] = []

    try:
        cmd = ["lsblk", "-o", "NAME,SIZE,TYPE,ROTA,MODEL,TRAN,MOUNTPOINTS", "-b", "-J"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            for dev in data.get("blockdevices", []):
                name = dev.get("name", "")
                # Ignore zram, ram, loop
                if name.startswith(("zram", "ram", "loop")):
                    continue
                dev_type = dev.get("type", "")
                if dev_type != "disk":
                    continue

                raw_size = dev.get("size", 0)
                size_bytes = int(raw_size) if str(raw_size).isdigit() else 0
                size_gib = round(size_bytes / (1024**3), 2)

                model = (dev.get("model") or "").strip()
                tran = dev.get("tran")
                rota = dev.get("rota")

                media_type, is_ssd, is_nvme = _classify_media(name, tran, rota, model)

                # Extract mountpoints from self or children
                mounts = dev.get("mountpoints") or []
                main_mount = mounts[0] if mounts else None

                def find_child_mount(children):
                    for ch in children:
                        cms = ch.get("mountpoints") or []
                        for m in cms:
                            if m == "/":
                                return "/"
                        if "children" in ch:
                            sub = find_child_mount(ch["children"])
                            if sub:
                                return sub
                    return None

                if "children" in dev and not main_mount:
                    c_mount = find_child_mount(dev["children"])
                    if c_mount:
                        main_mount = c_mount

                drive = StorageDrive(
                    name=name,
                    model=model or name,
                    size_bytes=size_bytes,
                    size_gib=size_gib,
                    media_type=media_type,
                    is_ssd=is_ssd,
                    is_nvme=is_nvme,
                    transport=tran,
                    mountpoint=main_mount,
                )
                drives.append(drive)
    except Exception:
        pass

    # Root filesystem metrics
    try:
        usage = shutil.disk_usage("/")
        info.root_total_gib = round(usage.total / (1024**3), 2)
        info.root_free_gib = round(usage.free / (1024**3), 2)
        info.root_used_gib = round(usage.used / (1024**3), 2)
        if usage.total > 0:
            info.root_used_percent = round((usage.used / usage.total) * 100, 1)
    except Exception:
        pass

    info.drives = drives
    info.total_disk_gib = round(sum(d.size_gib for d in drives), 2)
    info.has_nvme = any(d.is_nvme for d in drives)
    info.has_ssd = any(d.is_ssd for d in drives)

    if drives:
        # Prefer NVMe / SSD with root or largest
        nvme_drives = [d for d in drives if d.is_nvme]
        info.primary_drive = nvme_drives[0] if nvme_drives else drives[0]

    return info
