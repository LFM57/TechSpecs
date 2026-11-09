"""Command-line interface for TechSpecs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from techspecs import __version__
from techspecs.collectors import collect_specs
from techspecs.reporters import (
    generate_json_report,
    generate_markdown_report,
    render_dashboard,
)
from techspecs.scoring import evaluate_specs, run_quick_benchmark


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for CLI."""
    parser = argparse.ArgumentParser(
        prog="techspecs",
        description="In-depth computer hardware spec analyzer, power scoring engine, and baseline comparator.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"techspecs {__version__}",
    )
    parser.add_argument(
        "-b",
        "--benchmark",
        action="store_true",
        help="Run an empirical micro-benchmark (~1-2s) to calibrate real-world performance.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full hardware specs and scoring report in structured JSON format.",
    )
    parser.add_argument(
        "-m",
        "--markdown",
        nargs="?",
        const="",
        default=None,
        metavar="FILE",
        help="Generate a Markdown performance audit report. Writes to FILE if provided, else prints to stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Main CLI execution flow."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # 1. Collect hardware specs
    specs = collect_specs()

    # 2. Evaluate power score and baselines
    report = evaluate_specs(specs)

    # 3. Optional benchmark
    bench = None
    if args.benchmark:
        bench = run_quick_benchmark()
        report.benchmark_score = bench.overall_benchmark_score

    # 4. JSON Output Mode
    if args.json:
        json_str = generate_json_report(report, bench)
        print(json_str)
        return 0

    # 5. Markdown Output Mode
    if args.markdown is not None:
        md_str = generate_markdown_report(report, bench)
        if args.markdown:
            out_path = Path(args.markdown)
            out_path.write_text(md_str, encoding="utf-8")
            print(f"Report written to: {out_path.resolve()}", file=sys.stderr)
        else:
            print(md_str)
        return 0

    # 6. Default Rich Terminal Dashboard
    render_dashboard(report, bench)
    return 0


if __name__ == "__main__":
    sys.exit(main())
