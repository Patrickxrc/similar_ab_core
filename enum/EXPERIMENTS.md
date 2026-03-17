# Path-order comparison for similar (a,b)-core

This folder now includes scripts to compare two pipelines:

- Path 1 (`AB -> SIM`): run `(a,b)`-core first, then similarity filtering.
- Path 2 (`SIM -> AB`): run similarity filtering first, then `(a,b)`-core.

## 1) Single run

```bash
python enum/compare_sim_ab_paths.py <edge_file> <a> <b> <sim> <mode> jaccard
```

- `mode`: `both` / `sim_left` / `sim_right`
- output JSON includes final graph sizes and overlap metrics between Path 1 and Path 2.

## 2) Grid run (recommended)

```bash
python enum/run_path_comparison_grid.py \
  --graphs enum/graph/bi1,enum/graph/bi2,enum/graph/m_sa \
  --sim 0.2,0.3,0.4,0.5,0.6,0.7 \
  --ab 2:2,3:3,4:4,5:5,3:5,5:3,2:6,6:2 \
  --modes both,sim_left,sim_right \
  --out_csv enum/path_compare_results.csv
```

## Why overlap metrics are meaningful

- `edge_jaccard`: direct structural agreement of final subgraphs.
- `left/right node_jaccard`: side-specific agreement.
- `same_edges/same_left/same_right`: strict equality checks.

If overlap is low, path order changes the final result significantly.
