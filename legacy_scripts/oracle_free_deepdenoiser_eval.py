"""Evaluate DeepDenoiser on the exact oracle-free continuous cases."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from external_final_deepdenoiser_eval import (
    TARGET_LEN,
    bandpass_filter,
    best_lag_and_corr,
    clean_amp_ratio,
    deepdenoise_array,
    load_3c_mseed,
    load_model,
    make_template,
    output_vs_clean_snr,
    rms,
    write_csv,
)


FS = 100.0
P_IDX = 1000
EVENT_SIGNAL_LEN = 2000
CONTINUOUS_LEN = 9000


def make_continuous_noise(paths):
    chunks = [bandpass_filter(load_3c_mseed(path, TARGET_LEN)) for path in paths]
    stream = np.concatenate(chunks, axis=0)
    stream -= np.median(stream, axis=0, keepdims=True)
    return stream[:CONTINUOUS_LEN].astype(np.float32)


def inject_template(noise, template, onset, target_snr_db):
    event = template[P_IDX:P_IDX + EVENT_SIGNAL_LEN].copy()
    event_rms = rms(event[:1000])
    noise_seg = noise[onset:onset + 1000]
    scale = event_rms / ((10 ** (target_snr_db / 20.0)) * (rms(noise_seg) + 1e-12))
    scaled_noise = noise * scale
    clean = np.zeros_like(scaled_noise, dtype=np.float32)
    clean[onset:onset + len(event)] = event
    return (scaled_noise + clean).astype(np.float32), clean


def metrics(output, clean, mixture, onset):
    output_crop = output[onset - P_IDX:onset - P_IDX + TARGET_LEN]
    clean_crop = clean[onset - P_IDX:onset - P_IDX + TARGET_LEN]
    lag, corr = best_lag_and_corr(output_crop, clean_crop)
    mask = np.ones(len(output), dtype=bool)
    mask[max(0, onset - 200):min(len(mask), onset + EVENT_SIGNAL_LEN + 200)] = False
    return {
        "output_vs_clean_snr": output_vs_clean_snr(output_crop, clean_crop),
        "amp_ratio_clean": clean_amp_ratio(output_crop, clean_crop),
        "lag_s": lag,
        "corr_z": corr,
        "background_suppression_db": float(
            20 * np.log10(rms(mixture[mask]) / (rms(output[mask]) + 1e-12))
        ),
    }


def summarize(rows):
    record = {"method": "DeepDenoiser", "n": len(rows)}
    for metric in (
        "output_vs_clean_snr", "amp_ratio_clean", "lag_s", "corr_z",
        "background_suppression_db",
    ):
        values = np.asarray([float(row[metric]) for row in rows])
        values = values[np.isfinite(values)]
        record[f"{metric}_mean"] = float(values.mean())
        record[f"{metric}_std"] = float(values.std(ddof=1))
        record[f"{metric}_median"] = float(np.median(values))
        record[f"{metric}_q25"] = float(np.quantile(values, 0.25))
        record[f"{metric}_q75"] = float(np.quantile(values, 0.75))
    amp = np.asarray([float(row["amp_ratio_clean"]) for row in rows])
    record["amp_in_0p8_1p2_fraction"] = float(np.mean((amp >= 0.8) & (amp <= 1.2)))
    return [record]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case_csv", type=Path, required=True)
    parser.add_argument("--data_dir", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    parser.add_argument("--no_template_taper", action="store_true")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    with args.case_csv.open(newline="", encoding="utf-8-sig") as handle:
        all_rows = list(csv.DictReader(handle))
    cases = {}
    for row in all_rows:
        cases.setdefault(row["case_id"], row)

    model = load_model()
    output_rows = []
    for index, row in enumerate(cases.values(), 1):
        event_path = args.data_dir / "events" / row["event_template"]
        noise_paths = [args.data_dir / "mixed" / name for name in row["noise_files"].split(";")]
        noise = make_continuous_noise(noise_paths)
        template = make_template(
            load_3c_mseed(event_path, TARGET_LEN),
            taper=not args.no_template_taper,
        )
        onset = int(round(float(row["onset_s"]) * FS))
        mixture, clean = inject_template(noise, template, onset, float(row["target_snr_db"]))
        denoised = deepdenoise_array(model, mixture, station="SYN")
        result = {
            "case_id": row["case_id"],
            "event_template": row["event_template"],
            "station_template": row["station_template"],
            "noise_files": row["noise_files"],
            "station_noise": row["station_noise"],
            "onset_s": row["onset_s"],
            "target_snr_db": row["target_snr_db"],
            "method": "DeepDenoiser",
        }
        result.update(metrics(denoised, clean, mixture, onset))
        output_rows.append(result)
        print(f"[DeepDenoiser {index}/{len(cases)}]")

    write_csv(args.out_dir / "oracle_free_continuous_deepdenoiser_detail.csv", output_rows)
    summary = summarize(output_rows)
    write_csv(args.out_dir / "oracle_free_continuous_deepdenoiser_summary.csv", summary)
    print(summary[0])


if __name__ == "__main__":
    main()
