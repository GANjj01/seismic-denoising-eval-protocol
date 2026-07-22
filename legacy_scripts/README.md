# Legacy Paper Scripts

These scripts are included for provenance because they produced the paper-era
evaluation tables.  Some defaults still reference the original local Windows
workspace and should be overridden before use.

For new baselines, prefer the reusable package interface:

```text
src/blindspot_eval_protocol/
```

The intended migration path is:

1. implement a method that maps a 3C mixture to a same-shaped 3C output;
2. score it with the frozen final-real and oracle-free indices;
3. write rows matching `configs/report_card_schema.json`;
4. summarize with `src/blindspot_eval_protocol/report_card.py`.
