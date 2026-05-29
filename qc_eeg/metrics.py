from __future__ import annotations

from dataclasses import dataclass

import numpy as np


FREQ_BANDS = {
    "delta": (0.5, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
    "gamma": (30.0, 50.0),
}


@dataclass(frozen=True)
class EegRecord:
    record_id: str
    scenario: str
    sfreq: float
    channels: tuple[str, ...]
    data_uv: np.ndarray
    source: str = "synthetic demo"

    @property
    def duration_sec(self) -> float:
        return float(self.data_uv.shape[1] / self.sfreq)


def generate_demo_record(kind: str, seed: int = 42) -> EegRecord:
    """Generate an EEG-like record in microvolts for reproducible demo runs."""
    rng = np.random.default_rng(seed)
    sfreq = 250.0
    duration_sec = 12.0
    channels = ("Fp1", "Fz", "Cz", "Pz", "Oz")
    time = np.arange(0, duration_sec, 1 / sfreq)

    base = (
        18.0 * np.sin(2 * np.pi * 10.0 * time)
        + 6.0 * np.sin(2 * np.pi * 6.0 * time)
        + 3.0 * np.sin(2 * np.pi * 22.0 * time)
    )
    data = np.vstack(
        [
            base + rng.normal(0, 4.0 + i, size=time.size)
            for i in range(len(channels))
        ]
    )

    if kind == "noisy":
        data[1] += rng.normal(0, 85.0, size=time.size)
        data[1] += 50.0 * np.sin(2 * np.pi * 50.0 * time)
        record_id = "demo_noisy_fz"
    elif kind == "flat":
        data[3] = rng.normal(0, 0.12, size=time.size)
        record_id = "demo_flat_pz"
    elif kind == "clean":
        record_id = "demo_clean_rest"
    else:
        raise ValueError(f"Unknown demo record kind: {kind}")

    return EegRecord(
        record_id=record_id,
        scenario="Rest",
        sfreq=sfreq,
        channels=channels,
        data_uv=data,
    )


def compute_band_power(record: EegRecord) -> tuple[dict[str, float], np.ndarray, np.ndarray]:
    data = record.data_uv - record.data_uv.mean(axis=1, keepdims=True)
    freqs = np.fft.rfftfreq(data.shape[1], d=1.0 / record.sfreq)
    fft = np.fft.rfft(data, axis=1)
    psd = (np.abs(fft) ** 2) / (record.sfreq * data.shape[1])
    psd_mean = psd.mean(axis=0)

    band_power: dict[str, float] = {}
    for name, (fmin, fmax) in FREQ_BANDS.items():
        mask = (freqs >= fmin) & (freqs <= fmax)
        integrator = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
        band_power[name] = float(integrator(psd_mean[mask], freqs[mask])) if mask.any() else 0.0
    return band_power, freqs, psd_mean


def compute_channel_metrics(record: EegRecord) -> dict[str, dict[str, float | str]]:
    metrics: dict[str, dict[str, float | str]] = {}
    for idx, channel in enumerate(record.channels):
        signal = record.data_uv[idx]
        peak_to_peak = float(np.ptp(signal))
        std_uv = float(np.std(signal))
        mean_abs_uv = float(np.mean(np.abs(signal)))

        reasons: list[str] = []
        if peak_to_peak > 220.0 or std_uv > 55.0:
            reasons.append("high_amplitude_or_noise")
        if peak_to_peak < 1.0 or std_uv < 0.3:
            reasons.append("low_amplitude_flat")

        metrics[channel] = {
            "peak_to_peak_uv": peak_to_peak,
            "std_uv": std_uv,
            "mean_abs_uv": mean_abs_uv,
            "status": "BAD" if reasons else "OK",
            "reason": ", ".join(reasons) if reasons else "within_thresholds",
        }
    return metrics


def compute_record_metrics(record: EegRecord) -> dict[str, object]:
    band_power, freqs, psd_mean = compute_band_power(record)
    channel_metrics = compute_channel_metrics(record)
    bad_channels = [
        channel
        for channel, metrics in channel_metrics.items()
        if metrics["status"] == "BAD"
    ]

    dominant_frequency = float(freqs[int(np.argmax(psd_mean))])
    mean_amplitude = float(np.mean(np.abs(record.data_uv)))
    max_amplitude = float(np.max(np.ptp(record.data_uv, axis=1)))
    alpha_beta_ratio = band_power["alpha"] / (band_power["beta"] + 1e-12)
    theta_alpha_ratio = band_power["theta"] / (band_power["alpha"] + 1e-12)
    n_bad = len(bad_channels)
    status = "PASS" if n_bad == 0 else ("REVIEW" if n_bad <= 2 else "FAIL")

    return {
        "record_id": record.record_id,
        "source_data": record.source,
        "scenario": record.scenario,
        "duration_sec": round(record.duration_sec, 2),
        "sfreq_hz": record.sfreq,
        "n_channels": len(record.channels),
        "bad_channels": ", ".join(bad_channels),
        "n_bad_channels": n_bad,
        "qc_status": status,
        "mean_amplitude_uv": mean_amplitude,
        "max_amplitude_uv": max_amplitude,
        "dominant_frequency_hz": dominant_frequency,
        "alpha_beta_ratio": float(alpha_beta_ratio),
        "theta_alpha_ratio": float(theta_alpha_ratio),
        **{f"power_{name}": float(value) for name, value in band_power.items()},
    }


def demo_records() -> list[EegRecord]:
    return [
        generate_demo_record("clean", seed=12),
        generate_demo_record("noisy", seed=12),
        generate_demo_record("flat", seed=12),
    ]
