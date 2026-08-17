# A defect in the Etosha elephant collar data, and what it costs to fix

`reproduce.py` downloads the public dataset from the Movebank Data Repository,
locates a measurable instrument defect in it, identifies where the defect
lives, and sizes the remedy.

```
python3 reproduce.py
```

About 43 MB on first run, then cached. Needs pandas and numpy. Writes
`flagged-fixes.csv`, the list of fixes the analysis would discard, keyed by
collar and timestamp, so anyone can apply or reject the remedy without
rerunning anything.

## Correction, and what changed

**The first version of this repository read the result as a hardware defect:
two production batches of one collar model behaving differently. That reading
was wrong.** The observation was right, the mechanism was not.

The split by delivery batch is real and reproduces exactly. But 91.8 % of the
flagged pairs sit on the *first pair of a burst*, and the rate falls to zero in
2010 on collars still deployed. This is an acquisition behaviour that was
resolved in the field, not a sensor that degrades. The practical consequence is
much better than the hardware reading: no collar needs excluding, and the
remedy costs 1.00 % of the dataset rather than a quarter of it.

Everything below is computed by the script. Nothing is typed in by hand.

## The criterion

Two fixes 10 to 60 seconds apart implying a speed above 8 m/s, that is 29 km/h.
The documented sprint speed of a savanna elephant is around 25 km/h, so 29 is
deliberately generous.

The criterion is given no deployment date and no serial number. The split comes
out on its own; the batch column is only added at the end to name it.

## 1. The fleet splits in two

| Batch | Collars | Impossible pairs |
|-------|---------|------------------|
| serials AG004-AG013, deployed Oct 2008 | 8 | 3.66 % – 17.27 % |
| serials AG189-AG195, deployed 2009 | 7 | 0 – 0.0021 %, four at exactly zero |

No overlap and no borderline case: the two groups are separated by a factor of
about 1,700. Same manufacturer, same declared model, nothing in the metadata.

## 2. Where the defect lives

| Rank within burst | Pairs | Flagged | Share |
|---|---|---|---|
| 1st to 2nd fix | 593,523 | **29,441** | 4.96 % |
| 2nd to 3rd | 436,047 | 364 | 0.083 % |
| 3rd to 4th | 401,983 | 2,250 | 0.560 % |
| 4th to 5th | 1,675 | 2 | 0.119 % |
| 5th to 6th | 804 | 0 | 0.000 % |

**91.8 % of the anomalies are the first pair of a burst**, at sixty times the
rate of the second pair. That is the signature of a receiver emitting a
position before its solution has converged, after twenty minutes asleep.

## 3. The collar never waits

The wake schedule is a strict 1,200 s grid, so the delay of the first fix
against its expected wake time measures acquisition effort directly. That delay
is **zero at every burst length and on both batches**, median and both
quartiles alike.

The collar reports at its scheduled second whether or not it has a solution.
The mechanism above is therefore measured, not inferred. The same measurement
rules out a competing reading — that the true first fix simply goes unrecorded
in short bursts — because that would place the recorded first fix ten seconds
late, and it does not.

## 4. Two alternatives, both tested and rejected

**Degraded timestamps.** The repository notes that some segments lack seconds
precision, which would manufacture false jumps. For pairs 15 to 40 minutes
apart, the 99th percentile of implied speed is 0.94 m/s for the 2008 batch and
0.99 m/s for the 2009 one. Indistinguishable.

**Ageing hardware or batteries.** The rate would grow over time. It does the
opposite: 39.90 % in 2008, 16.44 % in 2009, then 0.0000 % in 2010 while those
collars were still returning tens of thousands of first-burst pairs. It did not
wear in; it was resolved.

## 5. What the remedy costs

| Remedy | Fixes removed | Share of dataset |
|---|---|---|
| discard every first fix of a burst | 753,046 | 25.7 % |
| discard first fixes that fail the physical test | **29,441** | **1.00 %** |

The blanket remedy throws away 723,605 sound positions and costs the 2009
collars a quarter of their data for nothing. The targeted one leaves 2,616
flagged pairs out of 2.93 million fixes, mostly on the *last* pair of a burst,
which this analysis does not explain.

Locating a defect is what makes a proportionate remedy possible. Without
knowing the anomalies sit on the first fix, the only safe options are to drop
whole collars or to accept the contamination.

## 6. Subsampling does not remove the defect. It selects it.

The defect is invisible at the cadence these data are normally analysed at.
Invisible is not harmless, and this is the part that matters if you hold data
like these.

**A resample to one sample per burst keeps the first fix** — that is what
`.first()` returns — which is exactly the fix carrying the defect. Of the
753,046 samples it yields, **29,441, or 3.91 %, are the contaminated fix**,
with a median position error of 241 m and a 90th percentile of 722 m.

**A speed or distance filter does not catch them.** At twenty-minute spacing,
241 m implies 0.20 m/s and 722 m implies 0.60 m/s: walking pace for an
elephant. A 2 m/s threshold removes **seven of the 29,441**. Subsampling
dilutes the error below every plausible threshold while keeping the position
error in full.

**The burst says which fix is wrong.** Over the 28,922 four-fix bursts whose
first pair is flagged, fix 1 sits a median of 242.7 m from the centroid of
fixes 2-3-4, while fix 2 sits 2.2 m from the centroid of fixes 3-4. A factor of
111, and fix 1 is the outlier in 100.0 % of them.

So the remedy costs nothing:

> **When subsampling a burst-sampled dataset, take the second fix of each
> burst rather than the first.**

One word in one line of code. No threshold, no species, no data discarded. What
it needs is knowing the defect is there.

## Why the criterion can be trusted

Applied unchanged to 287 public datasets from the same repository, it recovers
the documented precision gap between Argos and GPS without being told anything
about the positioning system: median 0.021 % of impossible pairs for Argos
against 0.001 % for GPS, Mann-Whitney p = 3.4e-07.

## What this is not

Not a claim about elephants, and not a criticism of the study these data
support, of the fieldwork behind them, or of their curation. It is a statement
about an instrument: a collar that reported positions before its receiver had
converged, in a published and cited dataset, and nobody had measured it.

## Data

Tsalyuk M, Kilian W, Reineking B, Getz W M et al., *African elephants in Etosha
National Park*, Movebank Data Repository.
Item `f30fb6d4-803f-4b45-8313-716c3b21e087`, CC BY-NC 4.0.
Associated paper: [10.1002/ecm.1348](https://doi.org/10.1002/ecm.1348).

The data are owned in the first instance by Etosha National Park, Namibia;
their collection was funded by the United States government through a research
award to W. M. Getz at the University of California, Berkeley; and M. Tsalyuk
curates the published deposit. This work is non-commercial.

`quality-sheet.md` is the one-page report this bench produces for any dataset.

---

If this measurement is wrong, I would rather know. Open an issue.
