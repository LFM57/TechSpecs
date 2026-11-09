# TechSpecs

> **In-depth hardware spec analyzer, power scoring engine, and baseline comparator.**

TechSpecs performs deep, unprivileged inspection of your computer's hardware (CPU, GPU, RAM, Storage, and Chassis), computes an objective **Power Score (0–100)** with workload-specific ratings, detects performance bottlenecks, and compares your system against standardized real-world baselines to determine whether your machine is *Very Weak*, *Modest / Entry-Level*, *Solid Mid-Range*, *Powerful*, *Very Powerful*, or an *Apex Workstation*.

---

## Features

- **Deep Hardware Inspection (Zero Root Required)**:
  - **CPU**: Model name, microarchitecture generation (Zen 2–5, Raptor/Arrow Lake, etc.), physical cores, logical threads, base & boost clocks, L1/L2/L3 caches, vector extensions (AVX, AVX2, AVX-512, FMA, AES).
  - **GPU**: Integrated (iGPU) vs Dedicated (dGPU) detection, vendor, architecture family, dedicated and shared VRAM, driver information.
  - **Memory**: Physical capacity, available memory, memory pressure, swap and ZRAM detection.
  - **Storage**: Drive topology, media classification (NVMe Gen3/Gen4/Gen5 SSD vs SATA SSD vs rotational HDD), capacity, partition layout.
  - **System & Chassis**: OS distribution, kernel version, chassis form factor (Laptop vs Desktop), battery charge & health condition.
- **Multi-Dimensional Power Scoring (0–100 Scale)**:
  - **Composite Power Score**: Weighted metric balancing CPU, GPU, RAM, and Storage with harmonic bottleneck penalties.
  - **Workload Suitability Profiles**: Specific ratings for *Everyday Productivity / Office*, *3D Gaming & Graphics*, *Software Engineering & Compiling*, and *AI / Machine Learning*.
  - **Hardware Bottleneck Detection**: Identifies system imbalances (e.g., low RAM or entry iGPU limiting performance) with upgrade impact recommendations.
- **Standardized Baseline Comparison**:
  - Automatically positions your computer on a spectrum among 6 reference baselines (from budget Chromebook to Apex RTX 4090 Workstation).
- **Fast Empirical Micro-Benchmark (`-b`)**:
  - Non-destructive ~1-second benchmark testing single-core math/hashing, parallel multi-core throughput, and memory bandwidth to corroborate hardware specifications.
- **Multiple Output Formats**:
  - Interactive **Rich Terminal Dashboard** (with automatic plain ANSI fallback).
  - Machine-readable **JSON Export** (`--json`).
  - GitHub-flavored **Markdown Audit Report** (`-m [FILE]`).

---

## Installation & Requirements

TechSpecs requires Python 3.10+ and standard Linux tools (`lscpu`, `lsblk`, `lspci`).

```bash
# Clone the repository
git clone https://github.com/louis-simonet/techspecs.git
cd techspecs

# Install in development mode
pip install -e .
```

---

## Usage

### 1. Interactive Terminal Dashboard
```bash
python3 -m techspecs
```
Displays the system overview, power score gauge, component breakdown table, workload suitability ratings, baseline spectrum chart, and bottleneck warnings.

### 2. Include Empirical Micro-Benchmark (`-b`)
```bash
python3 -m techspecs -b
```
Runs a rapid 1-second benchmark (single-core operations/sec, multi-core scaling factor, and memory bandwidth) alongside the theoretical spec analysis.

### 3. Structured JSON Export (`--json`)
```bash
python3 -m techspecs --json | jq .
```
Outputs the complete specification dictionary, component scores, workload ratings, bottlenecks, and baseline comparisons in structured JSON.

### 4. Markdown Audit Report (`-m`)
```bash
# Output to stdout
python3 -m techspecs -m

# Save directly to file
python3 -m techspecs -m audit_report.md
```

---

## Power Scoring Methodology

The Power Score is computed on an intuitive **0 to 100** scale based on modern computing standards:

$$\text{Power Score} = (0.38 \times \text{CPU}) + (0.32 \times \text{GPU}) + (0.18 \times \text{RAM}) + (0.12 \times \text{Storage}) - \text{Bottleneck Penalty}$$

### Component Weights & Factors
1. **CPU (38%)**: Physical cores & logical threads (scaled with diminishing returns via Amdahl's law), maximum boost frequency, microarchitecture IPC factor (Zen 2–5, Intel 10th–15th Gen), L3 cache capacity, and modern instruction set extensions (AVX2, AVX-512, FMA).
2. **GPU (32%)**: Hardware compute tier (ultra-budget iGPU to flagship discrete GPUs), architecture generation, and dedicated VRAM capacity.
3. **RAM (18%)**: Capacity curve (4 GB penalized, 8 GB basic, 16 GB standard, 32 GB enthusiast, 64 GB+ workstation) and ZRAM/swap protection.
4. **Storage (12%)**: NVMe Gen3/4/5 (highest) vs SATA SSD vs eMMC vs rotational HDD, adjusted for total capacity.
5. **Harmonic Bottleneck Penalty**: If a single component (such as RAM or GPU) falls far behind the rest of the system, a penalty of up to -8 pts is applied to reflect real-world user experience.

### Rating Tiers & Qualitative Verdicts
| Score Range | Tier Name | Qualitative Verdict | Typical Use Cases |
|---|---|---|---|
| **0 – 25** | Ultra-Budget / Minimal | **Very Weak** | Single-window browsing, basic terminal tasks, text editing. Struggles with multitasking. |
| **26 – 45** | Entry-Level / Everyday | **Modest / Entry-Level** | Daily office work, 1080p video streaming, light web multitasking, indie 2D games. |
| **46 – 65** | Solid Mid-Range | **Solid Mid-Range** | Smooth multitasking, 1080p gaming, web/app software development, photo editing. |
| **66 – 80** | High-Performance | **Powerful** | 1440p gaming, large software builds, local Docker virtualization, 4K media work. |
| **81 – 92** | Enthusiast / Creator | **Very Powerful** | 4K high-FPS gaming, 3D animation, deep learning inference, compile-intensive codebases. |
| **93 – 100** | Apex Workstation | **Apex Workstation** | Elite multi-core computing, AI model training, massive dataset crunching, simulations. |

---

## Standard Reference Baselines

TechSpecs measures your system against 6 curated hardware baselines:
1. **Budget Chromebook / Netbook** (Intel Celeron N4020, UHD 600, 4GB RAM, 64GB eMMC) — **Score: 14.5**
2. **Everyday Entry Laptop** (AMD Athlon Silver 7120U, Radeon 610M, 6GB RAM, 128GB NVMe) — **Score: 28.5**
3. **Modern Mainstream Office PC** (Intel Core i5-1335U, Iris Xe, 16GB RAM, 512GB NVMe) — **Score: 49.0**
4. **Mainstream Gaming & Dev Desktop** (AMD Ryzen 5 7600, RTX 4060 8GB, 32GB DDR5, 1TB NVMe) — **Score: 72.0**
5. **Enthusiast Gaming & Creator Rig** (AMD Ryzen 7 7800X3D, RTX 4070 Ti Super 16GB, 32GB DDR5, 2TB NVMe) — **Score: 86.5**
6. **Apex AI & 3D Workstation** (AMD Ryzen 9 7950X, RTX 4090 24GB, 64GB DDR5, 4TB NVMe Gen5) — **Score: 98.0**

---

## Running the Test Suite

```bash
pytest tests/ -v
```

All 21 unit and integration tests validate collector accuracy, mock hardware scoring scenarios, baseline comparisons, and CLI reporting.

---

## License

MIT License. Designed and crafted with precision.
