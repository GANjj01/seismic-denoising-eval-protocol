"""External-artifact E3 covariate rebuild entry point.

This wrapper is intentionally not the fresh-extract offline recomputation path.
It is for users who reacquire the FDSN waveforms or have an external sample
tensor archive and want to rebuild the covariate tables from waveform-level
artifacts. Raw MiniSEED files, saved sample tensors, and checkpoint weights are
not redistributed in the release package.

The v1.0.5 package-portable offline entry point is:

    python scripts/recompute_e3_adjustment_from_released_tables.py \
      --package-root <extracted-package-root> \
      --output-dir <temporary-output-dir>

External waveform/tensor rebuilding requires paths supplied explicitly through
future CLI arguments. No workstation path is hard-coded here.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--waveform-root", type=Path, help="Root containing reacquired waveform files, if available")
    parser.add_argument("--tensor-root", type=Path, help="External sample tensor archive, if available")
    parser.add_argument("--checkpoint-root", type=Path, help="External hash-identified checkpoint directory, if available")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for regenerated covariate outputs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    provided = [args.waveform_root, args.tensor_root, args.checkpoint_root]
    if not any(provided):
        raise SystemExit(
            "External waveform/tensor/checkpoint paths are required for waveform-level covariate rebuilding. "
            "Use recompute_e3_adjustment_from_released_tables.py for fresh-extract offline verification."
        )
    raise SystemExit(
        "Waveform-level covariate rebuilding is documented as an external-artifact pathway in v1.0.5, "
        "but the formal release package does not redistribute raw waveforms, tensors, or model weights. "
        "Use the package-portable recompute script for offline adjustment/bootstrap verification."
    )


if __name__ == "__main__":
    raise SystemExit(main())
