from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import Sequence

from .audio import MediaError
from .detector import OverlapDetectionError, detect_overlap
from .models import AnalysisConfig


def _quote_path(path: Path) -> str:
    return shlex.quote(str(path))


def _build_ffmpeg_examples(file1: Path, file2: Path, overlap_start: float, file2_overlap_end: float) -> tuple[str, str, str]:
    quoted_file1 = _quote_path(file1)
    quoted_file2 = _quote_path(file2)
    quoted_audio = shlex.quote("full_audio.m4a")
    cut_file1_output = shlex.quote("merged-cut-file1.mp4")
    cut_file2_output = shlex.quote("merged-cut-file2.mp4")
    keep_3s_output = shlex.quote("merged-keep-3s-overlap.mp4")
    concat_suffix = '[v0][v1]concat=n=2:v=1:a=0[v]'
    keep_overlap_seconds = min(3.0, file2_overlap_end)
    cut_file1_with_overlap = overlap_start + keep_overlap_seconds

    cut_file1 = (
        f"ffmpeg -i {quoted_file1} -i {quoted_file2} -i {quoted_audio} "
        f'-filter_complex "[0:v]trim=start=0:end={overlap_start:.3f},setpts=PTS-STARTPTS[v0];'
        f'[1:v]setpts=PTS-STARTPTS[v1];'
        f'{concat_suffix}" '
        f'-map "[v]" -map 2:a:0 -c:v libx264 -c:a aac -shortest {cut_file1_output}'
    )
    cut_file2 = (
        f"ffmpeg -i {quoted_file1} -i {quoted_file2} -i {quoted_audio} "
        f'-filter_complex "[0:v]setpts=PTS-STARTPTS[v0];'
        f'[1:v]trim=start={file2_overlap_end:.3f},setpts=PTS-STARTPTS[v1];'
        f'{concat_suffix}" '
        f'-map "[v]" -map 2:a:0 -c:v libx264 -c:a aac -shortest {cut_file2_output}'
    )
    keep_3s_overlap = (
        f"ffmpeg -i {quoted_file1} -i {quoted_file2} -i {quoted_audio} "
        f'-filter_complex "[0:v]trim=start=0:end={cut_file1_with_overlap:.3f},setpts=PTS-STARTPTS[v0];'
        f'[1:v]trim=start={keep_overlap_seconds:.3f},setpts=PTS-STARTPTS[v1];'
        f'{concat_suffix}" '
        f'-map "[v]" -map 2:a:0 -c:v libx264 -c:a aac -shortest {keep_3s_output}'
    )
    return cut_file1, cut_file2, keep_3s_overlap


def build_parser() -> argparse.ArgumentParser:
    defaults = AnalysisConfig()
    parser = argparse.ArgumentParser(
        prog="audio_overlap",
        description="Detect the overlapping audio region between two media files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("file1", type=Path, help="First media file")
    parser.add_argument("file2", type=Path, help="Second media file")
    parser.add_argument("--expected-overlap", type=float, default=defaults.expected_overlap, help="Expected overlap length in seconds")
    parser.add_argument("--search-window", type=float, default=None, help="Seconds to inspect at the tail/head boundaries")
    parser.add_argument("--min-overlap", type=float, default=None, help="Minimum credible overlap length in seconds")
    parser.add_argument("--coarse-sample-rate", type=int, default=defaults.coarse_sample_rate, help="Sample rate for coarse search")
    parser.add_argument("--fine-sample-rate", type=int, default=defaults.fine_sample_rate, help="Sample rate for refinement")
    parser.add_argument("--refine-margin", type=float, default=defaults.refine_margin, help="Seconds of margin around the coarse match")
    parser.add_argument("--min-score", type=float, default=defaults.min_score, help="Minimum normalized-correlation score to accept")
    parser.add_argument("--min-confidence", type=float, default=defaults.min_confidence, help="Minimum confidence score to accept")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = AnalysisConfig(
        expected_overlap=args.expected_overlap,
        search_window=args.search_window,
        min_overlap=args.min_overlap,
        coarse_sample_rate=args.coarse_sample_rate,
        fine_sample_rate=args.fine_sample_rate,
        refine_margin=args.refine_margin,
        min_score=args.min_score,
        min_confidence=args.min_confidence,
    )

    try:
        result = detect_overlap(args.file1, args.file2, config)
    except (MediaError, OverlapDetectionError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"file1_duration:      {result.file1_duration:.3f}s")
    print(f"file2_duration:      {result.file2_duration:.3f}s")
    print(f"file1_overlap_start: {result.file1_overlap_start:.3f}s")
    print(f"file1_overlap_end:   {result.file1_overlap_end:.3f}s")
    print(f"file2_overlap_start: {result.file2_overlap_start:.3f}s")
    print(f"file2_overlap_end:   {result.file2_overlap_end:.3f}s")
    print(f"relative_offset:     {result.relative_offset:.3f}s")
    print(f"overlap_duration:    {result.overlap_duration:.3f}s")
    print(f"score:               {result.score:.3f}")
    print(f"confidence:          {result.confidence:.3f}")
    cut_file1, cut_file2, keep_3s_overlap = _build_ffmpeg_examples(
        args.file1,
        args.file2,
        result.file1_overlap_start,
        result.file2_overlap_end,
    )
    print()
    print("# audio_source:       Replace full_audio.m4a with your full-length audio file")
    print()
    print("# ffmpeg_example_1:    Cut file1 at file1_overlap_start and append full file2")
    print()
    print(cut_file1)
    print()
    print("# ffmpeg_example_2:    Keep full file1 and append file2 after trimming file2_overlap_end")
    print()
    print(cut_file2)
    print()
    print("# ffmpeg_example_3:    Keep 3 seconds of the overlap on file1 and append file2 after trimming 3 seconds")
    print()
    print(keep_3s_overlap)
    return 0
