from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy.io import wavfile


def _write_wave(path: Path, samples: np.ndarray, sample_rate: int) -> None:
    peak = np.max(np.abs(samples))
    normalized = samples if peak == 0 else samples / peak
    wavfile.write(path, sample_rate, normalized.astype(np.float32))


class CLITests(unittest.TestCase):
    def test_help_shows_default_values(self) -> None:
        completed = subprocess.run(
            ["uv", "run", "audio_overlap", "-h"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("(default: 10.0)", completed.stdout)
        self.assertIn("(default: 4000)", completed.stdout)
        self.assertIn("(default: 16000)", completed.stdout)

    def test_cli_reports_overlap(self) -> None:
        sample_rate = 16000
        t_prefix = np.arange(sample_rate * 5, dtype=np.float64) / sample_rate
        t_overlap = np.arange(sample_rate * 10, dtype=np.float64) / sample_rate
        prefix = 0.35 * np.sin(2.0 * np.pi * 180.0 * t_prefix)
        overlap = 0.5 * np.sin(2.0 * np.pi * 440.0 * t_overlap) + 0.2 * np.sin(2.0 * np.pi * 660.0 * t_overlap)

        file1_samples = np.concatenate([prefix, overlap]).astype(np.float32)
        file2_samples = overlap.astype(np.float32)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            file1 = temp_path / "file1.wav"
            file2 = temp_path / "file2.wav"
            _write_wave(file1, file1_samples, sample_rate)
            _write_wave(file2, file2_samples, sample_rate)

            completed = subprocess.run(
                ["uv", "run", "audio_overlap", str(file1), str(file2)],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("file1_duration:", completed.stdout)
        self.assertIn("file2_duration:", completed.stdout)
        self.assertIn("file1_overlap_start:", completed.stdout)
        self.assertIn("overlap_duration:", completed.stdout)
        self.assertIn("ffmpeg_example_1:", completed.stdout)
        self.assertIn("ffmpeg_example_2:", completed.stdout)
        self.assertIn("ffmpeg_example_3:", completed.stdout)
        self.assertIn("audio_source:", completed.stdout)
        self.assertIn("full_audio.m4a", completed.stdout)
        self.assertIn("merged-cut-file1.mp4", completed.stdout)
        self.assertIn("merged-cut-file2.mp4", completed.stdout)
        self.assertIn("merged-keep-3s-overlap.mp4", completed.stdout)

    def test_cli_rejects_unrelated_audio(self) -> None:
        sample_rate = 16000
        t1 = np.arange(sample_rate * 12, dtype=np.float64) / sample_rate
        t2 = np.arange(sample_rate * 10, dtype=np.float64) / sample_rate
        file1_samples = (
            0.5 * np.sin(2.0 * np.pi * 145.0 * t1)
            + 0.2 * np.sin(2.0 * np.pi * 205.0 * t1 + 0.4)
            + 0.1 * np.sin(2.0 * np.pi * 285.0 * t1 + 0.8)
        ).astype(np.float32)
        file2_samples = (
            0.4 * np.sin(2.0 * np.pi * 430.0 * t2)
            + 0.2 * np.sin(2.0 * np.pi * 610.0 * t2 + 0.1)
        ).astype(np.float32)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            file1 = temp_path / "file1-error.wav"
            file2 = temp_path / "file2.wav"
            _write_wave(file1, file1_samples, sample_rate)
            _write_wave(file2, file2_samples, sample_rate)

            completed = subprocess.run(
                ["uv", "run", "audio_overlap", str(file1), str(file2)],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("No credible overlap found", completed.stderr)
