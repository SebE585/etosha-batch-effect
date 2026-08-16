# A batch effect in the Etosha elephant collar data

`reproduce.py` downloads the public dataset from the Movebank Data Repository
and applies one criterion to it. Two fixes 10 to 60 seconds apart implying a
speed above 8 m/s, that is 29 km/h. The documented sprint speed of a savanna
elephant is around 25 km/h, so 29 is deliberately generous.

```
python3 reproduce.py
```

About 43 MB on first run, then cached. Needs pandas and numpy.

## What comes out

The 15 collars split in two, with no overlap and no borderline case.

| Batch | Collars | Impossible pairs |
|-------|---------|------------------|
| serials AG004-AG013, deployed Oct 2008 | 8 | 3.66 % to 17.27 % |
| serials AG189-AG195, deployed 2009 | 7 | 0.00 % |

Same manufacturer, same declared model, nothing in the metadata. The criterion
is given no deployment date and no serial number: the split comes out on its
own, and the batch column is only added at the end to name it.

## The alternative that does not hold

The repository notes that some segments lack seconds precision, so degraded
timestamps in the older batch would manufacture false jumps. The script prints
the control: for pairs 15 to 40 minutes apart, the 99th percentile of implied
speed is 0.94 m/s for the 2008 batch and 0.99 m/s for the 2009 one.

Indistinguishable. The effect exists only inside the 10-second bursts, which is
why it stays invisible at the cadence these data are normally analysed at.

## Why the criterion can be trusted

Applied unchanged to 388 public datasets from the same repository, it recovers
the documented precision gap between Argos and GPS without being told anything
about the positioning system: median 0.021 % of impossible pairs for Argos
against 0.001 % for GPS, Mann-Whitney p = 3.4e-07.

## What this is not

Not a claim about elephants, and not a criticism of the study these data
support. It is a statement about the instruments: two production batches of one
collar model behave differently, and a file that pools them mixes two
populations of hardware.

The 2008 batch is old. What is not old is that this sits in a published, cited
dataset and had not been measured.

## Data

Tsalyuk M, Kilian W, Reineking B, Getz W M et al., *African elephants in Etosha
National Park*, Movebank Data Repository.
Item `f30fb6d4-803f-4b45-8313-716c3b21e087`, CC BY-NC 4.0.
Associated paper: [10.1002/ecm.1348](https://doi.org/10.1002/ecm.1348).

`quality-sheet.md` is the one-page report this bench produces for any dataset.

---

If this measurement is wrong, I would rather know. Open an issue.
