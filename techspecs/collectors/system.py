"""System, OS, chassis, and battery metadata collector."""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SystemInfo:
    hostname: str = "localhost"
    os_name: str = "Linux"
    os_version: str = ""
    kernel: str = ""
    architecture: str = ""
    manufacturer: str = "Unknown"
    product_name: str = "PC"
    chassis_type: str = "Desktop"
    has_battery: bool = False
    battery_charge_pct: float | None = None
    battery_health_pct: float | None = None


_CHASSIS_MAP = {
    "1": "Other",
    "2": "Unknown",
    "3": "Desktop",
    "4": "Low Profile Desktop",
    "5": "Pizza Box",
    "6": "Mini Tower",
    "7": "Tower",
    "8": "Portable",
    "9": "Laptop",
    "10": "Notebook / Laptop",
    "11": "Hand Held",
    "12": "Docking Station",
    "13": "All in One",
    "14": "Sub Notebook",
    "15": "Space-saving",
    "16": "Lunch Box",
    "17": "Main Server Chassis",
    "18": "Expansion Chassis",
    "19": "SubChassis",
    "20": "Bus Expansion Chassis",
    "21": "Peripheral Chassis",
    "22": "RAID Chassis",
    "23": "Rack Mount Chassis",
    "24": "Sealed-case PC",
    "30": "Tablet",
    "31": "Convertible",
    "32": "Detachable",
}


def _read_dmi_field(field_name: str) -> str:
    path = Path(f"/sys/class/dmi/id/{field_name}")
    if path.is_file():
        try:
            return path.read_text().strip()
        except Exception:
            pass
    return ""


def _collect_battery_info() -> tuple[bool, float | None, float | None]:
    """Inspect /sys/class/power_supply/ for laptop battery status."""
    ps_dir = Path("/sys/class/power_supply")
    if not ps_dir.is_dir():
        return False, None, None

    for bat in ps_dir.glob("BAT*"):
        try:
            charge = None
            cap_file = bat / "capacity"
            if cap_file.is_file():
                val = cap_file.read_text().strip()
                if val.isdigit():
                    charge = float(val)

            health = None
            # Check energy_full vs energy_full_design
            ef = bat / "energy_full"
            efd = bat / "energy_full_design"
            if ef.is_file() and efd.is_file():
                ef_val = float(ef.read_text().strip())
                efd_val = float(efd.read_text().strip())
                if efd_val > 0:
                    health = round((ef_val / efd_val) * 100, 1)

            # Alternatively charge_full vs charge_full_design
            if health is None:
                cf = bat / "charge_full"
                cfd = bat / "charge_full_design"
                if cf.is_file() and cfd.is_file():
                    cf_val = float(cf.read_text().strip())
                    cfd_val = float(cfd.read_text().strip())
                    if cfd_val > 0:
                        health = round((cf_val / cfd_val) * 100, 1)

            return True, charge, health
        except Exception:
            continue

    return False, None, None


def collect_system_info() -> SystemInfo:
    """Collect operating system, kernel, hardware chassis, and battery status."""
    info = SystemInfo()
    info.hostname = platform.node() or "localhost"
    info.kernel = platform.release() or ""
    info.architecture = platform.machine() or ""

    # Parse /etc/os-release
    os_file = Path("/etc/os-release")
    if os_file.is_file():
        try:
            for line in os_file.read_text().splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    v = v.strip(' "\'')
                    if k == "PRETTY_NAME":
                        info.os_name = v
                    elif k == "NAME" and info.os_name == "Linux":
                        info.os_name = v
                    elif k == "VERSION_ID":
                        info.os_version = v
        except Exception:
            pass

    # DMI information
    vendor = _read_dmi_field("sys_vendor")
    prod_name = _read_dmi_field("product_name")
    prod_version = _read_dmi_field("product_version")
    chassis_code = _read_dmi_field("chassis_type")

    if vendor:
        info.manufacturer = vendor

    if prod_version and prod_version not in ("None", "Default string"):
        info.product_name = prod_version
    elif prod_name and prod_name not in ("None", "Default string"):
        info.product_name = prod_name

    chassis = _CHASSIS_MAP.get(chassis_code, "")
    has_bat, charge, health = _collect_battery_info()
    info.has_battery = has_bat
    info.battery_charge_pct = charge
    info.battery_health_pct = health

    if chassis:
        info.chassis_type = chassis
    elif has_bat:
        info.chassis_type = "Laptop"
    else:
        info.chassis_type = "Desktop"

    return info
