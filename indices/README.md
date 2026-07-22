# Case Indices

The indices identify evaluation windows without redistributing MiniSEED files.

- `oracle_free_816_case_index.csv`: legacy-named index with one row per
  controlled reference-based mixture. It records the event template file name,
  station, noise file names, hidden onset, and target SNR.
- `final_real_272_event_index.csv`: one row per final real-event window.

To recreate raw waveforms, retrieve AM-network data through FDSN/Raspberry Shake
services using ObsPy.  The helper `scripts/fetch_raspberryshake_windows.py`
expects an index with explicit `station`, `starttime`, and `endtime` columns;
adapt it if your catalog starts from filename-derived timestamps.
