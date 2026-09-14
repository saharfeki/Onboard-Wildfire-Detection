"""Compute the B0 baseline data volume from a sensor YAML configuration.

Metric contract:
    B0  = baseline bytes per frame, before staged processing.
    B1  = bytes after Stage 1 filtering (not computed in this module).
    B2  = bytes after Stage 2 detection (not computed in this module).
    B3  = bytes after transmission packaging (not computed in this module).
    DRR = 1 - (B3 / B0), the data reduction ratio.
    CR  = B0 / B3, the end-to-end compression ratio.

This baseline-only implementation intentionally makes no assumptions about
Stage 1, Stage 2, or transmission packaging savings.
"""

from __future__ import annotations

import argparse
from math import ceil
from pathlib import Path
from typing import Any

import yaml


# Metric-contract constants. Values are descriptive because B1-B3 are not yet
# available in the baseline implementation.
B0 = "baseline bytes per frame"
B1 = "bytes after Stage 1 filtering (not computed yet)"
B2 = "bytes after Stage 2 detection (not computed yet)"
B3 = "bytes after transmission packaging (not computed yet)"
DRR = "1 - (B3 / B0)"
CR = "B0 / B3"

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "configs" / "sensor_config.yaml"


def load_sensor_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load a sensor configuration YAML file and return its mapping."""
    path = Path(config_path)
    with path.open("r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)
    if not isinstance(config, dict):
        raise ValueError(f"Sensor configuration must be a mapping: {path}")
    return config


def compute_baseline(config: dict[str, Any]) -> dict[str, Any]:
    """Return B0 sizing values in bytes, retaining all calculation inputs.

    Units at each arithmetic step:
    - bits_per_pixel_total: bits/pixel across all bands
    - bytes_per_frame_raw: bytes/frame
    - bytes_per_frame_comp: bytes/frame
    - bytes_per_frame_total (B0): bytes/frame
    - bytes_per_day: bytes/day
    """
    required = {
        "frame_width_px", "frame_height_px", "bands", "compression_ratio",
        "metadata_bytes_per_frame", "frames_per_day",
    }
    missing = sorted(required.difference(config))
    if missing:
        raise KeyError(f"Missing required sensor configuration keys: {', '.join(missing)}")

    frame_width_px = config["frame_width_px"]
    frame_height_px = config["frame_height_px"]
    bands = config["bands"]
    compression_ratio = config["compression_ratio"]
    metadata_bytes_per_frame = config["metadata_bytes_per_frame"]
    frames_per_day = config["frames_per_day"]

    if not isinstance(bands, list) or not bands:
        raise ValueError("bands must be a non-empty list of mappings")
    if not all(isinstance(band, dict) and "bit_depth" in band for band in bands):
        raise ValueError("each band must be a mapping with a bit_depth")
    if not all(isinstance(value, int) and value > 0 for value in (frame_width_px, frame_height_px)):
        raise ValueError("frame_width_px and frame_height_px must be positive integers")
    if not all(isinstance(band["bit_depth"], int) and band["bit_depth"] > 0 for band in bands):
        raise ValueError("each band bit_depth must be a positive integer")
    if compression_ratio <= 0:
        raise ValueError("compression_ratio must be greater than zero")

    band_count = len(bands)
    pixels_per_frame = frame_width_px * frame_height_px  # pixels/frame
    bits_per_pixel_total = sum(band["bit_depth"] for band in bands)  # bits/pixel
    bits_per_frame = pixels_per_frame * bits_per_pixel_total  # bits/frame
    # A partial final byte still occupies one byte on the wire; do not truncate it.
    bytes_per_frame_raw = (bits_per_frame + 7) // 8  # bytes/frame
    bytes_per_frame_comp = ceil(bytes_per_frame_raw / compression_ratio)  # bytes/frame
    bytes_per_frame_total = bytes_per_frame_comp + metadata_bytes_per_frame  # bytes/frame (B0)
    bytes_per_day = bytes_per_frame_total * frames_per_day  # bytes/day

    return {
        "name": config.get("name"),
        "platform": config.get("platform"),
        "gsd_m": config.get("gsd_m"),
        "frame_width_px": frame_width_px,
        "frame_height_px": frame_height_px,
        "bands": bands,
        "band_count": band_count,
        "compression_ratio": compression_ratio,
        "metadata_bytes_per_frame": metadata_bytes_per_frame,
        "frames_per_day": frames_per_day,
        "pixels_per_frame": pixels_per_frame,
        "bits_per_pixel_total": bits_per_pixel_total,
        "bits_per_frame": bits_per_frame,
        "bytes_per_frame_raw": bytes_per_frame_raw,
        "bytes_per_frame_comp": bytes_per_frame_comp,
        "bytes_per_frame_total": bytes_per_frame_total,
        "bytes_per_day": bytes_per_day,
    }


def format_baseline_table(result: dict[str, Any]) -> str:
    """Format the intermediate values as a clean, dependency-free table."""
    rows = [
        ("pixels_per_frame", result["pixels_per_frame"], "pixels/frame"),
        ("bits_per_pixel_total", result["bits_per_pixel_total"], "bits/pixel"),
        ("bytes_per_frame_raw", result["bytes_per_frame_raw"], "bytes/frame"),
        ("bytes_per_frame_comp", result["bytes_per_frame_comp"], "bytes/frame"),
        ("bytes_per_frame_total (B0)", result["bytes_per_frame_total"], "bytes/frame"),
        ("bytes_per_day", result["bytes_per_day"], "bytes/day"),
    ]
    name_width = max(len(name) for name, _, _ in rows)
    value_width = max(len(f"{value:,.2f}") for _, value, _ in rows)
    header = f"{'Metric':<{name_width}}  {'Value':>{value_width}}  Units"
    divider = "-" * len(header)
    lines = [header, divider]
    lines.extend(f"{name:<{name_width}}  {value:>{value_width},.2f}  {units}" for name, value, units in rows)
    return "\n".join(lines)


def main() -> None:
    """Load a configuration and print its B0 calculation."""
    parser = argparse.ArgumentParser(description="Compute a sensor B0 baseline.")
    parser.add_argument("config", nargs="?", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    print(format_baseline_table(compute_baseline(load_sensor_config(args.config))))


if __name__ == "__main__":
    main()
