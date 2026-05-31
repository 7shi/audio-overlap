# audio-overlap

## Overview

This project analyzes the overlapping segment between two video files by using **audio only**. The detected overlap will later be used to support safe and accurate concatenation of the videos.

## Requirements

### Goal

- Detect the overlapping time range shared by two video files.
- Use the audio tracks only for overlap detection.
- Provide data that can be used to join the two videos at the correct boundary.

### Functional Requirements

1. The script must accept two video files as input.
2. The script must extract or read the audio tracks from both files.
3. The script must compare the audio signals and detect the overlapping region.
4. The expected overlap length is approximately 10 seconds, but the implementation should tolerate some variation.
5. The script must report the most likely alignment between the two files.
6. The result should include enough information to determine where the first file ends and where the second file should continue.

### Input Requirements

- Input consists of two video files.
- The video content itself must not be used for overlap detection.
- The files may contain a partially duplicated section near the join point.

### Output Requirements

The script should output:

- the estimated overlap start/end or equivalent alignment information,
- the time offset between the two files,
- a confidence indicator or matching score if possible.

### Constraints

- Overlap detection must be based on audio data only.
- The solution should be designed for practical joining of real video files.
- The implementation should prioritize reliability over unnecessary complexity.

### Non-Goals

- Video-frame-based matching is out of scope.
- Automatic final muxing or rendering is not required in the first step.
