from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np


class MediaError(RuntimeError):
    """Raised when media probing or decoding fails."""


def probe_duration(path: Path) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
        )
    except FileNotFoundError as error:
        raise MediaError("ffprobe is required but was not found on PATH") from error

    if completed.returncode != 0:
        raise MediaError(completed.stderr.strip() or f"ffprobe failed for {path}")

    payload = json.loads(completed.stdout)
    duration_text = payload.get("format", {}).get("duration")
    if duration_text is None:
        raise MediaError(f"Could not determine duration for {path}")

    duration = float(duration_text)
    if duration <= 0:
        raise MediaError(f"Media duration must be positive for {path}")
    return duration


def extract_audio_segment(path: Path, start: float, duration: float, sample_rate: int) -> np.ndarray:
    if duration <= 0:
        return np.zeros(0, dtype=np.float32)

    command = [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{max(start, 0.0):.6f}",
        "-t",
        f"{duration:.6f}",
        "-i",
        str(path),
        "-vn",
        "-sn",
        "-dn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-f",
        "f32le",
        "-acodec",
        "pcm_f32le",
        "pipe:1",
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as error:
        raise MediaError("ffmpeg is required but was not found on PATH") from error

    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise MediaError(stderr or f"ffmpeg failed for {path}")

    audio = np.frombuffer(completed.stdout, dtype=np.float32)
    if audio.size == 0:
        raise MediaError(f"No audio samples were decoded from {path}")
    return audio.copy()
