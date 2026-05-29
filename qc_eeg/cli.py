from __future__ import annotations

import argparse
from pathlib import Path

from .metrics import compute_record_metrics, demo_records
from .reporting import (
    write_bad_channels_svg,
    write_band_power_svg,
    write_csv,
    write_html_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qc-eeg",
        description="Minimal EEG Quality Check prototype.",
    )
    subparsers = parser.add_subparsers(dest="command")

    demo = subparsers.add_parser("demo", help="Run QC on bundled synthetic demo records.")
    demo.add_argument(
        "--output",
        default="reports/demo_run",
        help="Directory for CSV, SVG and HTML outputs.",
    )
    return parser


def run_demo(output: Path) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    records = demo_records()
    metric_rows = [compute_record_metrics(record) for record in records]
    test_rows = _build_test_rows(metric_rows)

    metrics_csv = output / "qc_results.csv"
    tests_csv = output / "test_results.csv"
    report_html = output / "report.html"
    band_svg = output / "band_power.svg"
    bad_svg = output / "bad_channels.svg"

    write_csv(metrics_csv, metric_rows)
    write_csv(tests_csv, test_rows)
    write_band_power_svg(band_svg, metric_rows)
    write_bad_channels_svg(bad_svg, metric_rows)
    write_html_report(report_html, metric_rows, test_rows)

    return {
        "metrics_csv": metrics_csv,
        "tests_csv": tests_csv,
        "report_html": report_html,
        "band_power_svg": band_svg,
        "bad_channels_svg": bad_svg,
    }


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        args = parser.parse_args(["demo"])

    if args.command == "demo":
        outputs = run_demo(Path(args.output))
        print("EEG QC demo completed.")
        for name, path in outputs.items():
            print(f"{name}: {path}")
        return

    parser.error(f"Unknown command: {args.command}")


def _build_test_rows(metric_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_id = {str(row["record_id"]): row for row in metric_rows}
    checks = [
        ("Clean record keeps PASS status", "demo_clean_rest", "PASS", by_id["demo_clean_rest"]["qc_status"]),
        ("Noisy Fz record is flagged", "demo_noisy_fz", "Fz in bad_channels", by_id["demo_noisy_fz"]["bad_channels"]),
        ("Flat Pz record is flagged", "demo_flat_pz", "Pz in bad_channels", by_id["demo_flat_pz"]["bad_channels"]),
    ]
    rows = []
    for check, record_id, expected, actual in checks:
        actual_text = str(actual)
        passed = expected == actual_text or expected.split(" in ")[0] in actual_text
        rows.append(
            {
                "check": check,
                "source_data": record_id,
                "expected": expected,
                "actual": actual_text,
                "status": "PASS" if passed else "FAIL",
            }
        )
    return rows
