# Algorithm

This note explains the detector mainly from the mathematical side, with only minimal code excerpts to show where the main ideas appear in the implementation.

## Problem setup

Let the tail of `file1` be a discrete-time signal \(x[n]\) and the head of `file2` be \(y[n]\). The goal is to estimate the lag \(\tau\) such that the beginning of \(y[n]\) aligns with a suffix of \(x[n]\). If the two files really share an overlapping segment, then for the correct lag \(\tau^\*\),

\[
x[n+\tau^\*] \approx y[n]
\]

on the interval where both signals are present. This is a standard time-delay estimation problem.

The detector does not search the whole files uniformly. It assumes the overlap is near the **end of `file1`** and the **start of `file2`**, so the optimization is restricted to a tail window and a head window. Mathematically, that is a prior on the admissible range of \(\tau\): instead of searching everywhere, the search is concentrated where a splice is expected to occur.

## Similarity measure

The main scoring function is normalized cross-correlation. For a candidate lag \(\tau\), the idealized score is

\[
\rho(\tau)=
\frac{\sum_n x[n+\tau]\,y[n]}
{\sqrt{\sum_n x[n+\tau]^2}\sqrt{\sum_n y[n]^2}}.
\]

The numerator is large when the two waveforms have the same oscillatory structure. The denominator normalizes away most gain differences, so the score depends more on shape than on absolute loudness. Before this step, the waveform is mean-centered, which removes DC bias, and RMS-normalized, which makes the correlation more comparable across files with different levels.

Only non-negative lags are considered, and only lags with enough shared support are accepted. That minimum-overlap constraint matters because correlation values computed from very short intersections are unstable and easy to over-interpret.

## Why FFT appears

A naive evaluation of \(\rho(\tau)\) for every lag would be too expensive for long windows, since direct correlation scales roughly like the product of the two sequence lengths. The detector therefore uses the convolution theorem: correlation in the time domain can be computed through multiplication in the frequency domain, reducing the dominant cost to approximately \(O(N \log N)\).

The implementation point where this happens is small:

```python
lags = signal.correlation_lags(file1_tail.size, file2_head.size, mode="full")
correlation = signal.correlate(file1_tail, file2_head, mode="full", method="fft")
```

This FFT-based correlation produces a score for every candidate lag efficiently enough that the detector can afford a dense search.

## Varying overlap length

One subtlety is that the valid overlap length changes with the lag. If `file2` is shifted deeper into the tail of `file1`, fewer samples overlap. Because of that, the detector cannot use one fixed normalization denominator for all lags. Instead, it computes the energy of the actually overlapping suffix/prefix pair at each candidate lag and normalizes by those lag-specific energies. In effect, the detector uses a normalized cross-correlation whose support depends on \(\tau\).

This is why the algorithm tracks both a lag and an overlap length. Once the best lag is found, the overlap duration is simply the amount of valid shared support associated with that lag.

## Coarse-to-fine search

The optimization is solved in two passes. First, the signals are downsampled and the best lag is estimated on a coarse time grid. Then the detector returns to a higher sample rate and searches only in a small neighborhood around that first estimate.

Mathematically, this is a multiresolution approximation to the same maximization problem:

\[
\tau^\*=\arg\max_\tau \rho(\tau).
\]

The coarse pass finds the right basin of attraction cheaply; the fine pass improves temporal precision without paying the cost of a full high-resolution search over the entire window. This is especially useful because overlap detection needs both robustness and sub-second accuracy.

## From lag to timestamps

Once the refined lag is known, all reported timestamps follow from simple coordinate conversion. The lag gives the start of the overlap inside the tail window of `file1`; adding the overlap duration gives the end of that region. Because the current model assumes `file2` starts within the duplicated region, `file2_overlap_start` is reported as `0.0s`, and `file2_overlap_end` equals the detected overlap duration, clipped by the actual duration of `file2`.

So the CLI outputs are not estimated independently. They are deterministic quantities derived from:

1. the best lag
2. the valid overlap length
3. the absolute position of the tail window within `file1`

## Confidence and ambiguity

The highest correlation peak alone is not enough. Repetitive or quasi-periodic audio can produce several plausible lags, so the detector also looks at how clearly the best peak separates from the next-best candidate and whether the detected duration is plausible relative to `--expected-overlap`.

In the code, the confidence model is intentionally simple and heuristic:

```python
peak_component = float(np.clip((peak_score - 0.4) / 0.6, 0.0, 1.0))
separation_component = float(np.clip((peak_score - second_best_score) / 0.2, 0.0, 1.0))
duration_component = float(np.clip(overlap_duration / max(expected_overlap, _EPSILON), 0.0, 1.0))
```

This is not a calibrated probability model; it is a practical ambiguity filter. A good match should have a high main peak, enough separation from nearby alternatives, and an overlap length that is not wildly inconsistent with the prior expectation. If those conditions are not met, the detector returns `No credible overlap found`.

## Summary

The detector is best understood as a constrained time-shift estimator. It searches for the lag that maximizes normalized cross-correlation between the tail of one file and the head of the next, uses FFTs to make that search efficient, refines the estimate in a coarse-to-fine manner, and converts the resulting lag into splice timestamps. Everything else — overlap duration, confidence, and the suggested `ffmpeg` splice points — is derived from that central optimization problem.
