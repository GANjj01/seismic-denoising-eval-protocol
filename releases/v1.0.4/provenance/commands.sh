#!/usr/bin/env bash
source /d/anacona/Scripts/activate seismic
python "<revision_workspace>\analysis\scripts\reconstruct_e3_e5_no_taper.py" setup
python "<revision_workspace>\analysis\scripts\reconstruct_e3_e5_no_taper.py" manifest
python "<revision_workspace>\analysis\scripts\reconstruct_e3_e5_no_taper.py" run --experiment e3 --save-tensors
python "<revision_workspace>\analysis\scripts\reconstruct_e3_e5_no_taper.py" run --experiment e5 --save-tensors --no-deepdenoiser
python "<revision_workspace>\analysis\scripts\reconstruct_e3_e5_no_taper.py" summarize
