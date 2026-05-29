import unittest

import numpy as np

from qc_eeg.metrics import (
    compute_channel_metrics,
    compute_record_metrics,
    generate_demo_record,
)


class MetricsTests(unittest.TestCase):
    def test_clean_demo_record_has_no_bad_channels(self):
        record = generate_demo_record("clean", seed=10)

        result = compute_record_metrics(record)

        self.assertEqual(result["n_bad_channels"], 0)
        self.assertEqual(result["qc_status"], "PASS")
        self.assertGreater(result["power_alpha"], result["power_delta"])

    def test_noisy_demo_record_marks_noisy_channel(self):
        record = generate_demo_record("noisy", seed=10)

        result = compute_record_metrics(record)
        channel_metrics = compute_channel_metrics(record)

        self.assertGreaterEqual(result["n_bad_channels"], 1)
        self.assertIn("Fz", result["bad_channels"])
        self.assertEqual(channel_metrics["Fz"]["status"], "BAD")

    def test_flat_demo_record_marks_low_amplitude_channel(self):
        record = generate_demo_record("flat", seed=10)

        result = compute_record_metrics(record)

        self.assertIn("Pz", result["bad_channels"])
        self.assertGreater(result["theta_alpha_ratio"], 0)

    def test_band_power_columns_are_numeric(self):
        record = generate_demo_record("clean", seed=10)

        result = compute_record_metrics(record)

        for key in ["power_delta", "power_theta", "power_alpha", "power_beta", "power_gamma"]:
            self.assertIsInstance(result[key], float)
            self.assertTrue(np.isfinite(result[key]))


if __name__ == "__main__":
    unittest.main()
