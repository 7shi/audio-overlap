from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import signal

from .audio import extract_audio_segment, probe_duration
from .models import AnalysisConfig, OverlapResult

_EPSILON = 1e-9


class OverlapDetectionError(RuntimeError):
    """Raised when a credible overlap cannot be determined."""


@dataclass(frozen=True, slots=True)
class _Match:
    lag_samples: int
    overlap_samples: int
    score: float
    second_best_score: float


def detect_overlap(file1: Path, file2: Path, config: AnalysisConfig) -> OverlapResult:
    duration1 = probe_duration(file1)
    duration2 = probe_duration(file2)

    search_window = _resolved_search_window(config)
    fine_rate = config.fine_sample_rate

    tail_duration = min(duration1, search_window)
    head_duration = min(duration2, search_window)
    tail_start = max(0.0, duration1 - tail_duration)

    tail_audio = extract_audio_segment(file1, start=tail_start, duration=tail_duration, sample_rate=fine_rate)
    head_audio = extract_audio_segment(file2, start=0.0, duration=head_duration, sample_rate=fine_rate)

    return _detect_from_windows(
        tail_audio=tail_audio,
        head_audio=head_audio,
        tail_start_seconds=tail_start,
        file1_duration=duration1,
        file2_duration=duration2,
        sample_rate=fine_rate,
        config=config,
    )


def detect_overlap_from_audio(
    file1_audio: np.ndarray,
    file2_audio: np.ndarray,
    sample_rate: int,
    config: AnalysisConfig,
) -> OverlapResult:
    duration1 = len(file1_audio) / sample_rate
    duration2 = len(file2_audio) / sample_rate
    search_window = _resolved_search_window(config)

    tail_samples = min(len(file1_audio), int(round(search_window * sample_rate)))
    head_samples = min(len(file2_audio), int(round(search_window * sample_rate)))
    tail_start = duration1 - (tail_samples / sample_rate)

    tail_audio = np.asarray(file1_audio[-tail_samples:], dtype=np.float32)
    head_audio = np.asarray(file2_audio[:head_samples], dtype=np.float32)

    return _detect_from_windows(
        tail_audio=tail_audio,
        head_audio=head_audio,
        tail_start_seconds=tail_start,
        file1_duration=duration1,
        file2_duration=duration2,
        sample_rate=sample_rate,
        config=config,
    )


def _detect_from_windows(
    *,
    tail_audio: np.ndarray,
    head_audio: np.ndarray,
    tail_start_seconds: float,
    file1_duration: float,
    file2_duration: float,
    sample_rate: int,
    config: AnalysisConfig,
) -> OverlapResult:
    if tail_audio.size < 2 or head_audio.size < 2:
        raise OverlapDetectionError("Not enough audio for overlap detection")

    coarse_tail = _resample_audio(tail_audio, sample_rate, config.coarse_sample_rate)
    coarse_head = _resample_audio(head_audio, sample_rate, config.coarse_sample_rate)
    coarse_match = _match_overlap(
        coarse_tail,
        coarse_head,
        sample_rate=config.coarse_sample_rate,
        min_overlap_seconds=_resolved_min_overlap(config),
    )

    coarse_start_seconds = coarse_match.lag_samples / config.coarse_sample_rate
    coarse_overlap_seconds = coarse_match.overlap_samples / config.coarse_sample_rate

    refine_head_seconds = min(
        len(head_audio) / sample_rate,
        max(_resolved_min_overlap(config) + (2.0 * config.refine_margin), coarse_overlap_seconds + (2.0 * config.refine_margin)),
    )
    refine_head_samples = max(1, int(round(refine_head_seconds * sample_rate)))
    refine_head = head_audio[:refine_head_samples]

    refine_tail_offset_seconds = max(0.0, coarse_start_seconds - config.refine_margin)
    refine_tail_offset_samples = int(round(refine_tail_offset_seconds * sample_rate))
    refine_tail_seconds = min(
        (len(tail_audio) - refine_tail_offset_samples) / sample_rate,
        refine_head_seconds + config.refine_margin,
    )
    refine_tail_samples = max(1, int(round(refine_tail_seconds * sample_rate)))
    refine_tail = tail_audio[refine_tail_offset_samples : refine_tail_offset_samples + refine_tail_samples]

    fine_match = _match_overlap(
        refine_tail,
        refine_head,
        sample_rate=sample_rate,
        min_overlap_seconds=_resolved_min_overlap(config),
    )

    file1_overlap_start = tail_start_seconds + refine_tail_offset_seconds + (fine_match.lag_samples / sample_rate)
    overlap_duration = fine_match.overlap_samples / sample_rate
    file1_overlap_end = min(file1_duration, file1_overlap_start + overlap_duration)
    file2_overlap_start = 0.0
    file2_overlap_end = min(file2_duration, overlap_duration)
    confidence = _confidence_score(
        peak_score=fine_match.score,
        second_best_score=fine_match.second_best_score,
        overlap_duration=overlap_duration,
        expected_overlap=config.expected_overlap,
    )

    if fine_match.score < config.min_score or confidence < config.min_confidence:
        raise OverlapDetectionError(
            f"No credible overlap found (score={fine_match.score:.3f}, confidence={confidence:.3f})"
        )

    return OverlapResult(
        file1_duration=file1_duration,
        file2_duration=file2_duration,
        file1_overlap_start=file1_overlap_start,
        file1_overlap_end=file1_overlap_end,
        file2_overlap_start=file2_overlap_start,
        file2_overlap_end=file2_overlap_end,
        relative_offset=file1_overlap_start,
        overlap_duration=overlap_duration,
        score=fine_match.score,
        confidence=confidence,
    )


def _resolved_search_window(config: AnalysisConfig) -> float:
    if config.search_window is not None:
        return config.search_window
    return max(30.0, config.expected_overlap * 3.0)


def _resolved_min_overlap(config: AnalysisConfig) -> float:
    if config.min_overlap is not None:
        return config.min_overlap
    return max(2.0, config.expected_overlap * 0.5)


def _resample_audio(audio: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    if source_rate == target_rate:
        return np.asarray(audio, dtype=np.float64)

    factor = math.gcd(source_rate, target_rate)
    return signal.resample_poly(audio, up=target_rate // factor, down=source_rate // factor).astype(np.float64)


def _normalize_audio(audio: np.ndarray) -> np.ndarray:
    normalized = np.asarray(audio, dtype=np.float64)
    normalized = normalized - np.mean(normalized)

    rms = np.sqrt(np.mean(np.square(normalized)))
    if rms <= _EPSILON:
        raise OverlapDetectionError("Audio segment is effectively silent")
    return normalized / rms


def _match_overlap(
    file1_tail: np.ndarray,
    file2_head: np.ndarray,
    *,
    sample_rate: int,
    min_overlap_seconds: float,
) -> _Match:
    file1_tail = _normalize_audio(file1_tail)
    file2_head = _normalize_audio(file2_head)

    min_overlap_samples = int(round(min_overlap_seconds * sample_rate))
    if min_overlap_samples <= 0:
        raise OverlapDetectionError("Minimum overlap must be positive")

    lags = signal.correlation_lags(file1_tail.size, file2_head.size, mode="full")
    correlation = signal.correlate(file1_tail, file2_head, mode="full", method="fft")

    valid = lags >= 0
    lags = lags[valid]
    correlation = correlation[valid]
    overlaps = np.minimum(file1_tail.size - lags, file2_head.size)

    valid = overlaps >= min_overlap_samples
    if not np.any(valid):
        raise OverlapDetectionError("Search window is too small for the requested minimum overlap")

    lags = lags[valid]
    correlation = correlation[valid]
    overlaps = overlaps[valid]

    tail_energy_prefix = np.concatenate(([0.0], np.cumsum(np.square(file1_tail))))
    head_energy_prefix = np.concatenate(([0.0], np.cumsum(np.square(file2_head))))

    tail_energy = tail_energy_prefix[lags + overlaps] - tail_energy_prefix[lags]
    head_energy = head_energy_prefix[overlaps]
    scores = correlation / np.sqrt(np.maximum(tail_energy * head_energy, _EPSILON))

    best_index = int(np.argmax(scores))
    best_lag = int(lags[best_index])
    best_overlap = int(overlaps[best_index])
    best_score = float(scores[best_index])

    exclusion = max(int(sample_rate * 0.5), min_overlap_samples // 2)
    alternate = np.abs(lags - best_lag) > exclusion
    second_best_score = float(np.max(scores[alternate])) if np.any(alternate) else 0.0

    return _Match(
        lag_samples=best_lag,
        overlap_samples=best_overlap,
        score=best_score,
        second_best_score=second_best_score,
    )


def _confidence_score(*, peak_score: float, second_best_score: float, overlap_duration: float, expected_overlap: float) -> float:
    peak_component = float(np.clip((peak_score - 0.4) / 0.6, 0.0, 1.0))
    separation_component = float(np.clip((peak_score - second_best_score) / 0.2, 0.0, 1.0))
    duration_component = float(np.clip(overlap_duration / max(expected_overlap, _EPSILON), 0.0, 1.0))
    return (0.8 * peak_component) + (0.1 * separation_component) + (0.1 * duration_component)
