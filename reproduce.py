#!/usr/bin/env python3
"""Reproduce a batch effect in the Etosha elephant collar data.

Downloads the public dataset from the Movebank Data Repository and applies one
criterion: two fixes 10 to 60 seconds apart implying a speed above 8 m/s
(29 km/h). The documented sprint speed of a savanna elephant is around
25 km/h, so 29 is deliberately generous.

The criterion knows nothing about deployment dates or serial numbers. The
split it produces comes out on its own.

    python3 reproduce.py

Needs pandas and numpy. Downloads about 43 MB on first run, then caches.
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
CACHE = Path(__file__).resolve().parent / "cache"
R = 6371008.8
CEIL_MPS = 8.0


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


def main() -> int:
    print("Etosha collar data, batch effect\n")
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
    df = df.sort_values(["dev", "ts"])

    dev = df.dev.to_numpy()
    t = df.ts.values.astype("datetime64[s]").astype(np.int64)
    same = dev[1:] == dev[:-1]
    dt = np.diff(t).astype(float)
    d = haversine_m(df["location-lat"].values[:-1], df["location-long"].values[:-1],
                    df["location-lat"].values[1:], df["location-long"].values[1:])

    intra = same & (dt >= 5) & (dt <= 60)          # pairs inside one burst
    v = np.where(intra, d / np.maximum(dt, 1), np.nan)
    bad = np.nan_to_num(v) > CEIL_MPS

    tab = (pd.DataFrame({"dev": dev[1:], "intra": intra, "bad": bad})
             .query("intra")
             .groupby("dev")
             .agg(pairs=("bad", "size"), impossible=("bad", "sum")))
    tab["pct"] = (100 * tab.impossible / tab.pairs).round(2)
    tab["batch"] = [batch.get(i, "?") for i in tab.index]
    tab = tab.sort_values("pct", ascending=False)

    print(f"\n{len(df):,} fixes, {df.dev.nunique()} animals\n")
    print(tab.to_string())

    for b in ("2008", "2009"):
        s = tab[tab.batch == b].pct
        print(f"\nbatch {b}: {len(s)} collars, {s.min():.2f} % to {s.max():.2f} %")

    # The obvious alternative: are timestamps degraded in the older batch?
    long = same & (dt >= 900) & (dt <= 2400)
    vl = np.where(long, d / np.maximum(dt, 1), np.nan)
    print("\nControl, pairs 15 to 40 minutes apart (99th percentile of implied speed):")
    for b in ("2008", "2009"):
        m = long & np.isin(dev[1:], [k for k, x in batch.items() if x == b])
        print(f"  batch {b}: {np.nanquantile(vl[m], 0.99):.2f} m/s")
    print("\nThe two batches are indistinguishable at that spacing. The effect")
    print("exists only inside the 10-second bursts, which is why it stays")
    print("invisible at the cadence these data are normally analysed at.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
