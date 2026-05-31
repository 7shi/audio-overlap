from __future__ import annotations

import unittest

import numpy as np

from audio_overlap.detector import OverlapDetectionError, detect_overlap_from_audio
from audio_overlap.models import AnalysisConfig


def _make_signal(duration_seconds: float, sample_rate: int, seed: int, freqs: tuple[float, float, float] = (220.0, 331.0, 517.0)) -> np.ndarray:
    generator = np.random.default_rng(seed)
    t = np.arange(int(duration_seconds * sample_rate), dtype=np.float64) / sample_rate
    signal = (
        0.5 * np.sin(2.0 * np.pi * freqs[0] * t)
        + 0.3 * np.sin(2.0 * np.pi * freqs[1] * t + 0.2)
        + 0.2 * np.sin(2.0 * np.pi * freqs[2] * t + 1.1)
    )
    signal += 0.04 * generator.standard_normal(t.shape[0])
    return signal.astype(np.float32)


class DetectOverlapFromAudioTests(unittest.TestCase):
    def test_detects_expected_overlap(self) -> None:
        sample_rate = 16000
        overlap = 10.0
        prefix = _make_signal(110.0, sample_rate, seed=7)
        suffix = _make_signal(15.0, sample_rate, seed=11)

        file1 = np.concatenate([prefix, suffix], dtype=np.float32)
        file2 = suffix.copy()

        result = detect_overlap_from_audio(file1, file2, sample_rate, AnalysisConfig(expected_overlap=overlap))

        self.assertAlmostEqual(result.file1_overlap_start, 110.0, delta=0.05)
        self.assertAlmostEqual(result.file1_overlap_end, 125.0, delta=0.05)
        self.assertAlmostEqual(result.file2_overlap_end, 15.0, delta=0.05)
        self.assertGreater(result.score, 0.95)
        self.assertGreater(result.confidence, 0.9)

    def test_rejects_unrelated_audio(self) -> None:
        sample_rate = 16000
        file1 = _make_signal(120.0, sample_rate, seed=1)
        file2 = _make_signal(12.0, sample_rate, seed=99, freqs=(123.0, 456.0, 789.0))

        with self.assertRaises(OverlapDetectionError):
            detect_overlap_from_audio(file1, file2, sample_rate, AnalysisConfig(expected_overlap=10.0))
