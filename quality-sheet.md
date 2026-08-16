# Quality sheet: African elephants in Etosha National Park

Movebank Data Repository, item `f30fb6d4-803f-4b45-8313-716c3b21e087`.

## What the dataset carries

| | |
|---|---|
| Dominant sensor | gps |
| Fixes | 2,930,268 |
| Individuals | 15 |
| Span | 1978 days |
| Median cadence | 10 s |
| Dominant cadence | 10 s |
| Regularity | 52 % of intervals at the dominant step |
| 95th percentile of gaps | 20 min |

## Three quality measures

| Measure | Value | Reading |
|---|---|---|
| Position spikes | 0.000 % | nothing notable |
| Repeated positions | 2.17 % | frequent repeats |
| Coordinate grain | 8 decimals | precision preserved |

> **Why "position spikes 0.000 %" sits next to a 17 % figure in `README.md`.**
> They are two different detectors. The out-and-back detector above catches an
> isolated fix that forces the track to leave and come straight back, which is
> the general, species-free case. The batch effect is not that shape: those
> pairs imply an impossible speed without returning, so the corpus-wide
> detector does not see them and a physiological ceiling does. Neither is
> wrong; a single criterion would have missed one of the two.

## What this dataset does not support

- Pooling the 15 animals as one population of instruments: the collars
  delivered in 2008 and in 2009 differ by a factor of about 1,700 in
  gross-error rate. The cause is an acquisition behaviour resolved in the
  field in 2010, not a difference of hardware. See `README.md`.
- Fix counts as a measure of effort without care: 2.17 % of rows repeat
  the previous position exactly.

## Method

Out-and-back detector, no scale and no species: over three consecutive
positions A, B, C the excursion is `(AB + BC - AC) / 2`, compared to the
95th percentile of that individual's own step. A fix is flagged past ten
times its own yardstick.

Applied unchanged across the corpus, this detector recovers the documented
precision gap between Argos and GPS on its own, over the 287 datasets labelled
as one or the other, p = 3.4e-07,
without being told anything about the positioning system.

This bench judges neither the science nor the collection. It measures what
the published file carries, and what it does not.

---

*If this measurement is wrong, I would rather know.*