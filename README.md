# audio-overlap

Detect the overlapping audio region between two media files and report where the second file should continue from the first.

For a more detailed explanation of the mathematics and the relevant code paths, see [ALGORITHM.md](ALGORITHM.md).

## Requirements

- Python managed with `uv`
- System `ffmpeg` and `ffprobe` available on `PATH`

## Installation

### As a tool (recommended)

```bash
# Install as a tool
uv tool install https://github.com/7shi/audio-overlap.git

# Add ~/.local/bin to PATH if not already added
export PATH="$HOME/.local/bin:$PATH"
```

### From source

```bash
# Source installation with uv
git clone https://github.com/7shi/audio-overlap.git
cd audio-overlap
uv sync
```

**Note**: When using the source checkout, prefix commands with `uv run`, for example `uv run audio-overlap ...`.

## Run

```bash
audio-overlap file1.mp4 file2.mp4
```

Output fields:

- `file1_duration`, `file2_duration`: total input durations
- `file1_overlap_start`, `file1_overlap_end`: overlap range inside `file1`
- `file2_overlap_start`, `file2_overlap_end`: overlap range inside `file2`
- `relative_offset`: where `file2` should line up on the `file1` timeline
- `overlap_duration`: estimated duplicated duration
- `score`, `confidence`: matching quality indicators
- `ffmpeg_example_1`, `ffmpeg_example_2`, `ffmpeg_example_3`: example merge commands, not executed
- `audio_source`: placeholder for the full-length external audio file used in those commands

Example output:

```text
file1_duration:      123.563s
file2_duration:      72.747s
file1_overlap_start: 110.000s
file1_overlap_end:   123.563s
file2_overlap_start: 0.000s
file2_overlap_end:   13.563s
relative_offset:     110.000s
overlap_duration:    13.563s
score:               0.924
confidence:          0.899

# audio_source:       Replace full_audio.m4a with your full-length audio file

# ffmpeg_example_1:    Cut file1 at file1_overlap_start and append full file2

ffmpeg -i file1.mp4 -i file2.mp4 -i full_audio.m4a -filter_complex "[0:v]trim=start=0:end=110.000,setpts=PTS-STARTPTS[v0];[1:v]setpts=PTS-STARTPTS[v1];[v0][v1]concat=n=2:v=1:a=0[v]" -map "[v]" -map 2:a:0 -c:v libx264 -c:a aac -shortest merged-cut-file1.mp4

# ffmpeg_example_2:    Keep full file1 and append file2 after trimming file2_overlap_end

ffmpeg -i file1.mp4 -i file2.mp4 -i full_audio.m4a -filter_complex "[0:v]setpts=PTS-STARTPTS[v0];[1:v]trim=start=13.563,setpts=PTS-STARTPTS[v1];[v0][v1]concat=n=2:v=1:a=0[v]" -map "[v]" -map 2:a:0 -c:v libx264 -c:a aac -shortest merged-cut-file2.mp4

# ffmpeg_example_3:    Keep 3 seconds of the overlap on file1 and append file2 after trimming 3 seconds

ffmpeg -i file1.mp4 -i file2.mp4 -i full_audio.m4a -filter_complex "[0:v]trim=start=0:end=113.000,setpts=PTS-STARTPTS[v0];[1:v]trim=start=3.000,setpts=PTS-STARTPTS[v1];[v0][v1]concat=n=2:v=1:a=0[v]" -map "[v]" -map 2:a:0 -c:v libx264 -c:a aac -shortest merged-keep-3s-overlap.mp4
```

The command exits non-zero when no credible overlap is found.

### Notes

- Tuning options are available through `audio-overlap --help`.
- The emitted `ffmpeg` commands splice only video from `file1` / `file2` and map audio from a separate full-length file such as `full_audio.m4a`.

## Generated samples

Generate fixtures for manual checks:

```bash
make samples
```

This creates:

- `tests/samples/file1.wav` and `tests/samples/file2.wav` as a positive pair
- `tests/samples/file1-error.wav` and `tests/samples/file2.wav` as a negative pair
