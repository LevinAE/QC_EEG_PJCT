# QC EEG Minimal Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal runnable EEG QC prototype without neural networks.

**Architecture:** The prototype uses a small Python package with metrics, reporting and CLI modules. The default demo command generates synthetic EEG-like records, computes QC metrics and exports CSV, SVG and HTML artifacts.

**Tech Stack:** Python 3.10+, NumPy, stdlib `argparse`, `csv`, `unittest`.

---

### Task 1: Metrics

**Files:**
- Create: `qc_eeg/metrics.py`
- Test: `tests/test_metrics.py`

- [x] Write tests for clean, noisy and flat demo records.
- [x] Implement deterministic demo signal generation.
- [x] Implement band-power and channel-quality metrics.
- [x] Verify tests with `python -m unittest tests.test_metrics`.

### Task 2: Reporting

**Files:**
- Create: `qc_eeg/reporting.py`
- Create outputs under `reports/demo_run/`

- [x] Implement CSV export.
- [x] Implement SVG chart export for band power and bad-channel counts.
- [x] Implement HTML report with two tables and two charts.

### Task 3: CLI And Docs

**Files:**
- Create: `qc_eeg/cli.py`
- Create: `README.md`
- Create: `docs/prototype_description.md`

- [x] Implement `python -m qc_eeg demo --output reports/demo_run`.
- [x] Document quick start and current state.
- [x] Explain why torchinfo/Netron are not required for this no-NN version.
