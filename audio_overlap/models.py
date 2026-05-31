from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnalysisConfig:
    expected_overlap: float = 10.0
    search_window: float | None = None
    min_overlap: float | None = None
    coarse_sample_rate: int = 4000
    fine_sample_rate: int = 16000
    refine_margin: float = 1.5
    min_score: float = 0.6
    min_confidence: float = 0.45


@dataclass(frozen=True, slots=True)
class OverlapResult:
    file1_duration: float
    file2_duration: float
    file1_overlap_start: float
    file1_overlap_end: float
    file2_overlap_start: float
    file2_overlap_end: float
    relative_offset: float
    overlap_duration: float
    score: float
    confidence: float
