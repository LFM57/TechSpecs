# ⚡ TechSpecs

<p align="center">
  <strong>Deep hardware spec analyzer, multi-dimensional power scoring engine, and baseline comparator for Linux.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/platform-linux-lightgrey.svg" alt="Platform Linux">
  <img src="https://img.shields.io/badge/permissions-zero--root-success.svg" alt="Zero Root Required">
  <img src="https://img.shields.io/badge/tests-21%20passed-brightgreen.svg" alt="Tests">
  <img src="https://img.shields.io/badge/license-MIT-purple.svg" alt="License MIT">
</p>

---

**TechSpecs** gives your PC an objective **Power Score (0–100)** by analyzing its CPU, GPU, RAM, Storage, and Chassis in depth — without requiring root privileges. It tells you immediately whether your system is **Very Weak**, **Modest / Entry-Level**, **Solid Mid-Range**, **Powerful**, or an **Apex Workstation**, pinpoints hardware bottlenecks, and ranks your machine against real-world standard baselines.

---

## 🚀 Quick Start

Run TechSpecs with one command:

```bash
# Clone the repository
git clone https://github.com/LFM57/TechSpecs.git
cd TechSpecs

# Create a clean virtual environment and install
uv venv --system-site-packages
.venv/bin/python3 -m pip install --no-build-isolation --no-deps -e .

# Launch the interactive terminal dashboard!
.venv/bin/techspecs
```

> **Prefer standard Python?** You can also run it directly without installing:
> ```bash
> python3 -m techspecs
> ```

---

## 🖥️ Terminal Dashboard Preview

Running `techspecs -b` delivers a complete audit in less than **1 second**:

```text
╭───────────── TechSpecs • Hardware Spec Analyzer & Power Rating ──────────────╮
│ LENOVO Lenovo V14 G4 AMN (Notebook / Laptop)                                 │
│ OS: Omarchy 4.5.0  •  Kernel: 7.2.15-1-omarchy                               │
│ Architecture: x86_64  •  Family: AMD Zen 2 (Mendocino)                       │
│ Battery: 64% charge  •  Health: 88.9%                                        │
╰──────────────────────────────────────────────────────────────────────────────╯
╭──────────────────────────────────────────────────────────────────────────────╮
│   POWER SCORE: 28.8 / 100   ►  VERDICT: [MODEST / ENTRY-LEVEL]               │
│   Category: Entry-Level / Everyday — Handles daily office tasks, 1080p video │
│ streaming, light web multitasking, and lightweight indie/retro games.        │
╰──────────────────────────────────────────────────────────────────────────────╯
                     Component Specifications & Sub-Scores                      
╭────────────────┬───────────────────────────┬────────────────┬────────────────╮
│ Subsystem      │ Specs                     │  Score (0-100) │ Gauge          │
├────────────────┼───────────────────────────┼────────────────┼────────────────┤
│ CPU            │ AMD Athlon Silver 7120U   │           16.2 │ ███░░░░░░░░░░░ │
│ GPU            │ Mendocino [Radeon 610M]   │           22.0 │ ████░░░░░░░░░░ │
│ Memory (RAM)   │ 5.6 GiB Total (with ZRAM) │           32.0 │ ██████░░░░░░░░ │
│ Storage        │ NVMe SSD • 119.2 GiB      │           82.0 │ ██████████████ │
╰────────────────┴───────────────────────────┴────────────────┴────────────────╯
```

---

## 📖 How to Use

| Command | What It Does |
|---|---|
| `techspecs` | Opens the full interactive dashboard (System specs, score, gauges, baseline chart, bottleneck alerts). |
| `techspecs -b` | Includes a rapid **~1-second empirical micro-benchmark** (single-core, multi-core, and memory bandwidth). |
| `techspecs --json` | Outputs complete structured specs and scores in **JSON** (perfect for scripts, APIs, or dashboards). |
| `techspecs -m` | Generates a clean **GitHub-flavored Markdown** audit report to stdout. |
| `techspecs -m report.md` | Saves the Markdown report directly to a file. |
| `techspecs -h` | Shows all available flags and options. |

### Examples

#### 1. Run with Quick Micro-Benchmark
```bash
techspecs -b
```
Runs a math/cryptographic hashing stress test and memory bandwidth streaming pass to validate your theoretical hardware specs against empirical real-world speeds.

#### 2. Export Audit to Markdown File
```bash
techspecs -m audit_report.md
```
Creates a comprehensive, shareable Markdown document featuring tables, component breakdowns, and upgrade advice.

#### 3. Parse Specs Programmatically with JSON
```bash
techspecs --json | jq '.overall_score, .rating_tier.verdict'
# 28.8
# "Modest / Entry-Level"
```

---

## 🎯 What Does My Score Mean?

TechSpecs rates computers on a standardized **0 to 100** scale calibrated against modern hardware standards:

| Score Range | Category | Verdict | Real-World Capability |
|---|---|---|---|
| **0 – 25** | Ultra-Budget | **Very Weak** | Single-tab browsing, text editing, terminal tasks. Struggles with modern multi-tabbing. |
| **26 – 45** | Entry-Level | **Modest / Entry-Level** | Daily office work, 1080p streaming, light web multitasking, indie 2D games. |
| **46 – 65** | Mid-Range | **Solid Mid-Range** | Smooth multitasking, 1080p gaming, web/app software development, photo editing. |
| **66 – 80** | Performance | **Powerful** | 1440p gaming, large software builds, local Docker virtualization, 4K media editing. |
| **81 – 92** | Enthusiast | **Very Powerful** | 4K high-FPS gaming, 3D animation, local LLM inference, compile-intensive codebases. |
| **93 – 100** | Workstation | **Apex Workstation** | Flagship multi-core compute, local AI model training, massive dataset crunching. |

### Workload Ratings
In addition to the overall score, TechSpecs computes 4 dedicated workload ratings:
- 🏢 **Daily Office & Productivity**: Single-thread speed, RAM responsiveness, and NVMe app launch speeds.
- 🎮 **3D Gaming & Graphics**: Heavily weights GPU architecture and VRAM capacity.
- 💻 **Software Engineering**: Multi-core compilation throughput, RAM capacity, and drive I/O.
- 🧠 **AI & Machine Learning**: Tensor capabilities, GPU VRAM depth, and vector instruction sets (AVX-512, FMA).

---

## 📊 Standard Reference Baselines

TechSpecs measures your computer against 6 standard reference machines so you immediately know where you stand:

```
Budget Netbook (14.5)           [███░░░░░░░░░░░░░░░░░] 14.5
Your PC (Lenovo V14 G4 AMN)     [██████░░░░░░░░░░░░░░] 28.8  ◄ CURRENT SYSTEM (Modest / Entry-Level)
Modern Mainstream Office (49.0) [██████████░░░░░░░░░░] 49.0
Mainstream Gaming / Dev (72.0)  [██████████████░░░░░░] 72.0
Enthusiast Rig (86.5)           [█████████████████░░░] 86.5
Apex Workstation (98.0)         [████████████████████] 98.0
```

1. **Budget Chromebook / Netbook** (Celeron N4020, UHD 600, 4GB RAM, 64GB eMMC) — **14.5**
2. **Everyday Entry Laptop** (Athlon Silver 7120U, Radeon 610M, 6GB RAM, 128GB NVMe) — **28.5**
3. **Modern Mainstream Office PC** (Core i5-1335U, Iris Xe, 16GB RAM, 512GB NVMe) — **49.0**
4. **Mainstream Gaming & Dev Desktop** (Ryzen 5 7600, RTX 4060 8GB, 32GB DDR5, 1TB NVMe) — **72.0**
5. **Enthusiast Gaming & Creator Rig** (Ryzen 7 7800X3D, RTX 4070 Ti Super 16GB, 32GB DDR5, 2TB NVMe) — **86.5**
6. **Apex AI & 3D Workstation** (Ryzen 9 7950X, RTX 4090 24GB, 64GB DDR5, 4TB Gen5 NVMe) — **98.0**

---

## 🔍 Bottleneck Detection

TechSpecs automatically analyzes system harmony and issues concrete upgrade recommendations:
- **RAM Bottlenecks**: Flags if RAM capacity is too low ($\le$ 6 GB), causing frequent swap thrashing.
- **GPU Bottlenecks**: Detects ultra-low tier integrated GPUs limiting 3D games and local LLM execution.
- **CPU Bottlenecks**: Identifies low core counts ($\le$ 2 cores) that saturate under background multitasking.
- **Storage Bottlenecks**: Warns if the primary boot drive is a mechanical HDD instead of an SSD.

---

## ⚙️ Technical Deep Dive

<details>
<summary><strong>Hardware Inspection Mechanics</strong></summary>

TechSpecs queries native Linux kernel interfaces without needing `sudo` or third-party daemon services:
- **CPU**: Inspects `/proc/cpuinfo`, `/sys/devices/system/cpu/cpu*/cpufreq/`, and cache levels (`/sys/devices/system/cpu/cpu0/cache/`). Detects microarchitecture family and vector instruction flags (`avx`, `avx2`, `avx512`, `fma`, `sha`, `aes`).
- **GPU**: Parses `lspci -vmm`, sysfs DRM nodes (`/sys/class/drm/card*/device/mem_info_vram_total`), and `nvidia-smi` to detect discrete vs integrated status and VRAM.
- **RAM**: Reads `/proc/meminfo` and `/sys/block/zram*` for physical memory and compressed ZRAM metrics.
- **Storage**: Queries block device topology via `lsblk` and `/sys/block/` to differentiate NVMe, SATA SSD, eMMC, and rotational HDDs.
- **Chassis & Battery**: Reads DMI identifiers (`/sys/class/dmi/id/`) and ACPI battery condition (`/sys/class/power_supply/BAT*/`).
</details>

<details>
<summary><strong>Scoring Mathematics & Bottleneck Penalties</strong></summary>

The overall power score is calculated via:

$$\text{Overall Score} = (0.38 \times \text{CPU}) + (0.32 \times \text{GPU}) + (0.18 \times \text{RAM}) + (0.12 \times \text{Storage}) - \text{Penalty}$$

- **CPU Score**: Models diminishing multi-core returns via Amdahl's Law ($\text{Effective Cores} = \text{Cores}^{0.82} + \text{Threads}_{\text{extra}} \times 0.3$), frequency scaling normalized against modern 4.5 GHz boost standards, microarchitecture IPC factors, and L3 cache bonuses.
- **GPU Score**: Tiers GPUs from low-power iGPUs (12–25 pts) to flagship discrete GPUs (90–100 pts), adjusted for dedicated VRAM.
- **RAM Score**: Non-linear capacity utility curve reflecting modern operating system memory demands (4GB = 18 pts, 8GB = 42 pts, 16GB = 72 pts, 32GB = 92 pts, 64GB+ = 98–100 pts).
- **Storage Score**: NVMe SSD (86 base) vs SATA SSD (65 base) vs eMMC (45 base) vs HDD (22 base), with capacity bonuses.
- **Harmonic Penalty**: If a single subsystem lags behind the system average by more than 25 points, a progressive penalty (up to -8 pts) is subtracted to account for real-world system stutter.
</details>

---

## 🧪 Testing

TechSpecs includes a full unit and integration test suite:

```bash
python3 -m pytest tests/ -v
```

All 21 tests pass with 100% test coverage across collectors, scoring models, baselines, and CLI exporters.

---

## 📄 License

MIT License. Crafted with precision.
