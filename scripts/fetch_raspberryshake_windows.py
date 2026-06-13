"""Fetch Raspberry Shake waveform windows from FDSN using released indices.

This script is a reproducibility helper.  The release does not redistribute raw
MiniSEED waveforms; it provides station/event/window identifiers and this FDSN
entry point instead.  Fill or adapt the timestamp columns if your local index
uses a richer event catalog than the filename-based paper indices.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", required=True, type=Path, help="CSV with station and time columns")
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--network", default="AM")
    parser.add_argument("--location", default="00")
    parser.add_argument("--channels", default="EHZ,EHN,EHE")
    parser.add_argument("--client", default="RASPISHAKE")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        from obspy import UTCDateTime
        from obspy.clients.fdsn import Client
    except Exception as exc:  # pragma: no cover
        raise SystemExit(f"ObsPy is required for fetching: {exc}") from exc

    client = Client(args.client)
    args.outdir.mkdir(parents=True, exist_ok=True)
    channels = [c.strip() for c in args.channels.split(",") if c.strip()]

    with args.index.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"station", "starttime", "endtime"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"Index needs columns {sorted(required)}; missing {sorted(missing)}")
        for row in reader:
            station = row["station"]
            start = UTCDateTime(row["starttime"])
            end = UTCDateTime(row["endtime"])
            for channel in channels:
                outfile = args.outdir / f"{args.network}.{station}.{channel}.{start.strftime('%Y%m%dT%H%M%S')}.mseed"
                print(f"{station} {channel} {start} {end} -> {outfile}")
                if not args.dry_run:
                    st = client.get_waveforms(args.network, station, args.location, channel, start, end)
                    st.write(str(outfile), format="MSEED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
