# Baseline Controls

The reusable baseline transforms live in:

```text
src/blindspot_eval_protocol/baselines.py
```

Included controls:

- `Identity`: output equals input; required for detecting pass-through models.
- `AdvScale`: global shrink, useful for showing that background suppression can
  be gamed without improving waveform recovery.
- `AdvShrink`: soft-thresholding diagnostic.
- `adv_gate_quantile`: dependency-light quantile energy-gating diagnostic.
- `adv_gate_sta_lta`: manuscript-exact STA/LTA AdvGate implementation.
- `adv_gate`: backward-compatible alias for `adv_gate_quantile`.

## Manuscript-exact AdvGate

The manuscript Table 4 and Figure 5 AdvGate results use a fixed STA/LTA trigger
over the three-component energy trace:

```text
energy = norm(x, axis=-1)
cft = obspy.signal.trigger.classic_sta_lta(energy, int(0.5 * fs), int(10.0 * fs))
gate = cft > 2.5
```

Use `blindspot_eval_protocol.baselines.adv_gate_sta_lta` for the reusable
function.  The paper-era reproduction script is:

```text
legacy_scripts/adversarial_baselines_eval.py
```

Its `adversarial_outputs()` function explicitly maps the manuscript `AdvGate`
row to `adv_gate_sta_lta`.  On the original workstation, the non-destructive
rerun command was:

```bat
call D:\anacona\Scripts\activate.bat seismic
python revision_workspace\analysis\scripts\run_advgate_sta_lta_audit.py ^
  --data_dir C:\Users\Administrator\Desktop\transformer_train\rs_external_2025pre ^
  --out_dir revision_workspace\audit\advgate_rerun_sta_lta ^
  --exclude_stations R3E8B R57B0 R6468 R6995 RF4CA ^
  --snr_levels -5 0 5 ^
  --seed 20260611
```

The full waveform rerun requires raw AM MiniSEED files, NumPy, SciPy, and
ObsPy.  The released `environments/environment-seismic.yml` includes ObsPy
1.5.0, and `pyproject.toml` exposes the optional
`manuscript-advgate` dependency group.  Expected numeric agreement with the
archived CSV outputs is within `5e-5` absolute or `1e-6` relative tolerance,
covering platform-level floating-point and BLAS differences.

Archived manuscript outputs:

```text
experiments/results/adversarial_baselines/adversarial_report_card.csv
experiments/results/adversarial_baselines/adversarial_real_events_summary.csv
experiments/results/adversarial_baselines/adversarial_oracle_free_summary.csv
experiments/results/adversarial_baselines/adversarial_real_events_detail.csv
experiments/results/adversarial_baselines/adversarial_oracle_free_detail.csv
paper/artifacts/figure_advgate_diagnostic_waveform.png
```

## Dependency-light AdvGate

`adv_gate_quantile` keeps samples whose three-component energy is above a fixed
quantile.  It is a portable demonstration baseline for smoke tests and simple
report-card examples.  It is not the implementation that generated manuscript
Table 4 or Figure 5, and its outputs should not be cited as reproductions of the
paper AdvGate row.

The public `adv_gate` name is retained as a backward-compatible alias to
`adv_gate_quantile`.  New code should call `adv_gate_quantile` or
`adv_gate_sta_lta` explicitly.

## Legacy Mapping

| Purpose | Path or function |
| --- | --- |
| Manuscript-exact function | `blindspot_eval_protocol.baselines.adv_gate_sta_lta` |
| Dependency-light function | `blindspot_eval_protocol.baselines.adv_gate_quantile` |
| Backward-compatible public alias | `blindspot_eval_protocol.baselines.adv_gate` |
| Paper-era full evaluation script | `legacy_scripts/adversarial_baselines_eval.py` |
| Paper-era script mapping | `AdvGate -> adv_gate_sta_lta` |
