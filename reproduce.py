#!/usr/bin/env python3
"""Locate a defect in the Etosha elephant collar data, and size its remedy.

Downloads the public dataset from the Movebank Data Repository and applies one
criterion: two fixes 10 to 60 seconds apart implying a speed above 8 m/s
(29 km/h). The documented sprint speed of a savanna elephant is around
25 km/h, so 29 is deliberately generous.

The criterion knows nothing about deployment dates or serial numbers. The
split it produces comes out on its own.

Then it asks where in the burst the flagged pairs sit, and whether the collar
delays its first fix. Those two answers change what the split means, and what
it costs to fix.

    python3 reproduce.py

Needs pandas and numpy. Downloads about 43 MB on first run, then caches.
Writes flagged-fixes.csv: the fixes this analysis would discard, keyed by
collar and timestamp, so you can apply or reject the remedy yourself.
"""

from __future__ import annotations

import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

API = "https://datarepository.movebank.org/server/api"
ITEM = "f30fb6d4-803f-4b45-8313-716c3b21e087"   # Etosha, Tsalyuk et al.
UA = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
R = 6371008.8
CEIL_MPS = 8.0
BURST_GAP_S = 60.0      # a gap longer than this starts a new burst
WAKE_PERIOD_S = 1200.0  # measured, not assumed: the modal spacing of bursts


def bitstreams() -> dict[str, str]:
    """Name -> download URL, for the published files of the item."""
    def get(url):
        req = urllib.request.Request(url, headers=UA)
        return json.load(urllib.request.urlopen(req, timeout=120))

    out = {}
    for b in get(f"{API}/core/items/{ITEM}/bundles")["_embedded"]["bundles"]:
        if b["name"] != "ORIGINAL":
            continue
        for x in get(b["_links"]["bitstreams"]["href"])["_embedded"]["bitstreams"]:
            out[x["name"]] = x["_links"]["content"]["href"]
    return out


def fetch(name: str, url: str) -> Path:
    CACHE.mkdir(exist_ok=True)
    path = CACHE / name.replace(" ", "_")
    if not path.exists():
        print(f"  downloading {name} ...", flush=True)
        urllib.request.urlretrieve(url, path)
    return path


def haversine_m(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = (np.sin((p2 - p1) / 2) ** 2
         + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2)
    return 2 * R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def rule(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


def main() -> int:
    print("Etosha collar data: locating a defect and sizing its remedy\n")
    files = bitstreams()

    ref_name = next(n for n in files if "reference-data" in n)
    gps_name = next(n for n in files if n.endswith(".csv.zip"))
    ref = pd.read_csv(fetch(ref_name, files[ref_name]))
    gps_path = fetch(gps_name, files[gps_name])

    # Batch is read off the tag serial, not off anything the criterion sees.
    batch = {str(r["animal-id"]): ("2008" if int(str(r["tag-id"])[2:]) < 100
                                   else "2009")
             for _, r in ref.iterrows()}

    with zipfile.ZipFile(gps_path) as z:
        member = next(n for n in z.namelist() if n.endswith(".csv"))
        print(f"  reading {member} ...", flush=True)
        df = pd.read_csv(z.open(member), low_memory=False, usecols=[
            "timestamp", "location-lat", "location-long",
            "individual-local-identifier", "visible"])

    df = df[df["visible"].astype(str).str.lower() == "true"]
    df = df.dropna(subset=["location-lat", "location-long"])
    df["ts"] = pd.to_datetime(df.timestamp, format="mixed", utc=True)
    df["dev"] = df["individual-local-identifier"].astype(str)
    df = df.sort_values(["dev", "ts"]).reset_index(drop=True)

    dev = df.dev.to_numpy()
    t = df.ts.values.astype("datetime64[s]").astype(np.int64)
    same = dev[1:] == dev[:-1]
    dt = np.diff(t).astype(float)
    d = haversine_m(df["location-lat"].values[:-1], df["location-long"].values[:-1],
                    df["location-lat"].values[1:], df["location-long"].values[1:])

    intra = same & (dt >= 5) & (dt <= 60)          # pairs inside one burst
    v = np.where(intra, d / np.maximum(dt, 1), np.nan)
    bad = np.nan_to_num(v) > CEIL_MPS

    # Burst identity and the rank of each fix inside its burst.
    new_burst = (~same) | (dt > BURST_GAP_S)
    bid = np.concatenate([[0], np.cumsum(new_burst)])
    s = pd.Series(bid)
    rank = s.groupby(s).cumcount().to_numpy()
    size = s.map(s.value_counts()).to_numpy()

    pairs = pd.DataFrame({
        "dev": dev[:-1],
        "batch": [batch.get(x, "?") for x in dev[:-1]],
        "rank": rank[:-1],                 # 0 = first fix of the burst
        "burst_size": size[:-1],
        "year": pd.DatetimeIndex(df.ts.values[:-1]).year,
        "intra": intra,
        "bad": bad,
    })
    pairs = pairs[pairs.intra].copy()

    n_flagged = int(pairs.bad.sum())
    print(f"\n{len(df):,} fixes, {df.dev.nunique()} animals, "
          f"{len(pairs):,} intra-burst pairs, {n_flagged:,} flagged")

    # ---------------------------------------------------------------- 1
    rule("1. The fleet splits in two, and the split matches the delivery batches")
    tab = pairs.groupby("dev").agg(pairs=("bad", "size"), impossible=("bad", "sum"))
    tab["pct"] = (100 * tab.impossible / tab.pairs).round(4)
    tab["batch"] = [batch.get(i, "?") for i in tab.index]
    print(tab.sort_values("pct", ascending=False).to_string())
    for b in ("2008", "2009"):
        s_ = tab[tab.batch == b].pct
        zero = int((tab[tab.batch == b].impossible == 0).sum())
        print(f"  batch {b}: {len(s_)} collars, {s_.min():.4f} % to {s_.max():.4f} % "
              f"({zero} at exactly zero)")
    print("\n  Same manufacturer, same declared model, nothing in the metadata.")
    print("  The criterion is given no serial and no deployment date.")

    # ---------------------------------------------------------------- 2
    rule("2. But it is not a hardware story: 92 % of it is the first pair")
    by_rank = pairs.groupby("rank").agg(pairs=("bad", "size"), flagged=("bad", "sum"))
    by_rank["pct"] = (100 * by_rank.flagged / by_rank.pairs).round(3)
    by_rank.index = [f"{i+1} -> {i+2}" for i in by_rank.index]
    print(by_rank.to_string())
    first = pairs[pairs["rank"] == 0]
    share = 100 * int(first.bad.sum()) / n_flagged
    print(f"\n  {share:.1f} % of all flagged pairs are the first pair of a burst.")
    assert int(by_rank.flagged.sum()) == n_flagged, "rank table does not sum to the total"

    # ---------------------------------------------------------------- 3
    rule("3. The collar never waits: first-fix delay against the wake schedule")
    starts = pd.DataFrame({"bid": bid, "dev": dev, "t": t,
                           "size": size, "rank": rank})
    starts = starts[starts["rank"] == 0].sort_values(["dev", "t"])
    starts["batch"] = [batch.get(x, "?") for x in starts.dev]
    period = float(starts.groupby("dev").t.diff().mode().iloc[0])
    starts["delay"] = starts.t - (starts.groupby("dev").t.shift(1) + period)
    win = starts[starts.delay.between(-120, 300)]
    print(f"  measured wake period: {period:.0f} s")
    print(win[win.batch == "2008"].groupby("size").delay.agg(
        n="size", median="median",
        q25=lambda x: x.quantile(0.25), q75=lambda x: x.quantile(0.75)).to_string())
    print("\n  Zero at every burst length, quartiles included. The collar reports at")
    print("  its scheduled second whether or not its solution has converged.")
    print("  That also rules out the reading that the true first fix goes")
    print("  unrecorded in short bursts: that would place it ten seconds late.")

    # ---------------------------------------------------------------- 4
    rule("4. Two alternatives, both tested and rejected")
    long = same & (dt >= 900) & (dt <= 2400)
    vl = np.where(long, d / np.maximum(dt, 1), np.nan)
    print("  Degraded timestamps? 99th percentile of implied speed, pairs 15-40 min apart:")
    for b in ("2008", "2009"):
        m = long & np.isin(dev[1:], [k for k, x in batch.items() if x == b])
        print(f"    batch {b}: {np.nanquantile(vl[m], 0.99):.2f} m/s")
    print("  Indistinguishable at that spacing.\n")
    print("  Ageing hardware? First-pair flag rate by year (%):")
    yr = (first.pivot_table(index="year", columns="batch", values="bad",
                            aggfunc="mean") * 100).round(4)
    print(yr.to_string())
    print("\n  It falls to zero rather than growing. It did not wear in; it was resolved.")

    # ---------------------------------------------------------------- 5
    rule("5. What the remedy costs")
    n_bursts = int(pd.Series(bid).nunique())
    n_targeted = int(first.bad.sum())
    n_fix = len(df)
    print(f"  discard every first fix of a burst      "
          f"{n_bursts:>9,}  {100*n_bursts/n_fix:5.1f} % of the dataset")
    print(f"  discard first fixes that fail the test  "
          f"{n_targeted:>9,}  {100*n_targeted/n_fix:5.2f} % of the dataset")
    print(f"\n  The blanket remedy throws away {n_bursts - n_targeted:,} sound positions.")
    print(f"  The targeted one leaves {n_flagged - n_targeted:,} flagged pairs, mostly on")
    print("  the last pair of a burst, which this analysis does not explain.")
    print("  No collar needs excluding and no animal needs dropping.")

    # The list, so anyone can apply or reject the remedy without rerunning this.
    idx = first.index[first.bad]
    out = pd.DataFrame({
        "device_id": df.dev.values[idx],
        "discarded_fix_ts": df.ts.values[idx + 1],
        "reason": f"first fix of burst, implied speed > {CEIL_MPS} m/s",
    }).sort_values(["device_id", "discarded_fix_ts"])
    assert len(out) == n_targeted
    out.to_csv(HERE / "flagged-fixes.csv", index=False)
    print(f"\n  Written: flagged-fixes.csv ({len(out):,} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
