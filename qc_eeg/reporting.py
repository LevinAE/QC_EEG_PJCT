from __future__ import annotations

import csv
import html
from pathlib import Path
from typing import Iterable

from .metrics import FREQ_BANDS


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def write_band_power_svg(path: Path, rows: list[dict[str, object]]) -> None:
    bands = list(FREQ_BANDS)
    width, height = 900, 460
    left, top, plot_w, plot_h = 86, 58, 720, 300
    colors = ["#2f6fed", "#0f9d7a", "#d9822b"]
    values = [
        [float(row[f"power_{band}"]) for band in bands]
        for row in rows
    ]
    max_value = max(max(v) for v in values) or 1.0
    group_w = plot_w / len(bands)
    bar_w = group_w / (len(rows) + 1)

    parts = _svg_header(width, height, "Band power by EEG frequency range")
    parts.append(_axes(left, top, plot_w, plot_h, "Frequency band", "Power, uV^2/Hz"))
    for band_idx, band in enumerate(bands):
        x0 = left + band_idx * group_w + bar_w * 0.5
        parts.append(f'<text x="{left + band_idx * group_w + group_w / 2:.1f}" y="{top + plot_h + 32}" text-anchor="middle" font-size="13">{band.title()}</text>')
        for row_idx, row in enumerate(rows):
            value = float(row[f"power_{band}"])
            bar_h = (value / max_value) * plot_h
            x = x0 + row_idx * bar_w
            y = top + plot_h - bar_h
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w * 0.78:.1f}" height="{bar_h:.1f}" fill="{colors[row_idx % len(colors)]}"/>')

    parts.extend(_legend(rows, colors, 825, 88))
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_bad_channels_svg(path: Path, rows: list[dict[str, object]]) -> None:
    width, height = 900, 430
    left, top, plot_w, plot_h = 86, 58, 700, 270
    max_value = max(int(row["n_bad_channels"]) for row in rows) or 1
    colors = {"PASS": "#0f9d7a", "REVIEW": "#d9822b", "FAIL": "#c0392b"}
    bar_w = plot_w / (len(rows) * 1.6)

    parts = _svg_header(width, height, "Detected bad EEG channels")
    parts.append(_axes(left, top, plot_w, plot_h, "Record", "Bad channels, count"))
    for idx, row in enumerate(rows):
        value = int(row["n_bad_channels"])
        bar_h = (value / max_value) * plot_h if max_value else 0
        x = left + idx * (plot_w / len(rows)) + bar_w * 0.35
        y = top + plot_h - bar_h
        status = str(row["qc_status"])
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" fill="{colors[status]}"/>')
        parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" font-size="13">{value}</text>')
        label = html.escape(str(row["record_id"]))
        parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{top + plot_h + 30}" text-anchor="middle" font-size="12">{label}</text>')

    parts.append('<rect x="815" y="78" width="14" height="14" fill="#0f9d7a"/><text x="838" y="90" font-size="13">PASS</text>')
    parts.append('<rect x="815" y="105" width="14" height="14" fill="#d9822b"/><text x="838" y="117" font-size="13">REVIEW</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_html_report(path: Path, metric_rows: list[dict[str, object]], test_rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    metric_columns = [
        "record_id",
        "scenario",
        "duration_sec",
        "sfreq_hz",
        "n_channels",
        "n_bad_channels",
        "bad_channels",
        "mean_amplitude_uv",
        "alpha_beta_ratio",
        "qc_status",
    ]
    test_columns = ["check", "source_data", "expected", "actual", "status"]
    body = f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>EEG QC prototype report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2933; }}
    h1, h2 {{ color: #17324d; }}
    table {{ border-collapse: collapse; width: 100%; margin: 14px 0 28px; }}
    th, td {{ border: 1px solid #cbd2d9; padding: 8px 10px; text-align: left; }}
    th {{ background: #eef2f7; }}
    .source {{ font-size: 14px; color: #52606d; margin-top: -8px; }}
    img {{ max-width: 100%; border: 1px solid #d9e2ec; margin: 10px 0 26px; }}
  </style>
</head>
<body>
  <h1>Quality Check EEG: демонстрационный отчёт прототипа</h1>
  <p>Отчёт сформирован минимальным прототипом QC для проверки структуры результатов, расчёта метрик сигнала и подготовки материалов для практики.</p>

  <h2>Таблица 1. Сводные QC-метрики по записям</h2>
  <p class="source">Источник данных: синтетические EEG-подобные записи, сгенерированные модулем qc_eeg.metrics.</p>
  {_html_table(metric_rows, metric_columns)}

  <h2>Таблица 2. Результаты тестирования прототипа</h2>
  <p class="source">Источник данных: демонстрационный запуск CLI на clean/noisy/flat сценариях.</p>
  {_html_table(test_rows, test_columns)}

  <h2>Рисунок 1. Спектральная мощность по частотным диапазонам</h2>
  <p class="source">Оси: X - диапазон частот, Y - мощность. Легенда показывает записи.</p>
  <img src="band_power.svg" alt="Band power chart">

  <h2>Рисунок 2. Количество проблемных каналов</h2>
  <p class="source">Оси: X - запись, Y - число каналов. Цвет отражает итоговый QC-статус.</p>
  <img src="bad_channels.svg" alt="Bad channels chart">
</body>
</html>
"""
    path.write_text(body, encoding="utf-8")


def _html_table(rows: list[dict[str, object]], columns: Iterable[str]) -> str:
    cols = list(columns)
    head = "".join(f"<th>{html.escape(col)}</th>" for col in cols)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{html.escape(_format_cell(row.get(col, '')))}</td>" for col in cols)
        body_rows.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def _format_cell(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _svg_header(width: int, height: int, title: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="30" text-anchor="middle" font-size="22" font-weight="700">{html.escape(title)}</text>',
    ]


def _axes(left: int, top: int, plot_w: int, plot_h: int, x_label: str, y_label: str) -> str:
    bottom = top + plot_h
    return "\n".join(
        [
            f'<line x1="{left}" y1="{bottom}" x2="{left + plot_w}" y2="{bottom}" stroke="#263238" stroke-width="1.5"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#263238" stroke-width="1.5"/>',
            f'<text x="{left + plot_w / 2}" y="{bottom + 72}" text-anchor="middle" font-size="15">{html.escape(x_label)}</text>',
            f'<text x="20" y="{top + plot_h / 2}" transform="rotate(-90 20 {top + plot_h / 2})" text-anchor="middle" font-size="15">{html.escape(y_label)}</text>',
        ]
    )


def _legend(rows: list[dict[str, object]], colors: list[str], x: int, y: int) -> list[str]:
    parts = ['<text x="815" y="65" font-size="13" font-weight="700">Legend</text>']
    for idx, row in enumerate(rows):
        yy = y + idx * 26
        label = html.escape(str(row["record_id"]))
        parts.append(f'<rect x="{x}" y="{yy}" width="14" height="14" fill="{colors[idx % len(colors)]}"/>')
        parts.append(f'<text x="{x + 22}" y="{yy + 12}" font-size="12">{label}</text>')
    return parts
