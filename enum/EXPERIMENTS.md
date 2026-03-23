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

## Relative-change metrics (new)

- `edge_retention_p1_vs_original`, `edge_retention_p2_vs_original`: how much of original edges remain in each path.
- `sim_after_ab_ratio`: extra shrink from SIM after AB-core in Path 1.
- `ab_after_sim_ratio`: extra shrink from AB after SIM-filtering in Path 2.
- `final_edge_path_gap`, `final_left_path_gap`, `final_right_path_gap`: normalized final gap between the two paths.

## Extra real-world style dataset in this repo

- Added `enum/graph/movietweetings_5k` (5,000 user-movie edges) converted from MovieTweetings `ratings.dat`.
- File format matches this project directly: each non-comment line is `<left_id> <right_id>`.
- You can run it immediately, e.g.:

```bash
python enum/compare_sim_ab_paths.py enum/graph/movietweetings_5k 3 3 0.3 both jaccard
```

## 3) Visualization for PPT / conclusion slides

You can generate intuitive plots directly from either:
- grid output CSV (`enum/path_compare_results.csv`), or
- summary CSV (`enum/ppt_6case_summary.csv`).

```bash
python enum/plot_path_comparison.py enum/path_compare_results.csv --out_dir enum/figures
# or
python enum/plot_path_comparison.py enum/ppt_6case_summary.csv --out_dir enum/figures_6case
```

The script outputs three PNG figures:
- `edge_jaccard_heatmaps.png`: sim × (a,b) heatmaps grouped by mode.
- `final_edge_gap_curves.png`: how path-difference changes with sim.
- `path1_path2_edge_curves.png`: final edge counts of Path1 vs Path2.

## Update: unified LEFT-SIM mode + r1/r2/r3/r4

The current Python runner now fixes similarity mode to **left-side only** (`sim_left`).
No `both/sim_right` switch is required.

Run one algorithm:

```bash
python enum/compare_sim_ab_paths.py <edge_file> <a> <b> <sim> jaccard --algo r1
python enum/compare_sim_ab_paths.py <edge_file> <a> <b> <sim> jaccard --algo r2
python enum/compare_sim_ab_paths.py <edge_file> <a> <b> <sim> jaccard --algo r3 --max_iter 20 --ab_step 0
python enum/compare_sim_ab_paths.py <edge_file> <a> <b> <sim> jaccard --algo r4 --max_iter 20 --sim_step 0
```

Batch-run over a grid:

```bash
python enum/run_path_comparison_grid.py \
  --graphs data/processed/edges_random50k.txt \
  --sim 0.10,0.12,0.14,0.16,0.18,0.20 \
  --ab 1:1,1:2,2:1,2:2,2:3,3:3 \
  --algos r1,r2,r3,r4 \
  --out_csv enum/path_compare_results.csv
```

## Build GT communities (overlapping) from labels

Example (HF metadata):

```bash
python enum/build_gt_communities.py \
  --edges data/processed/edges_random50k.txt \
  --meta_source hf \
  --meta_config raw_meta_Electronics \
  --out data/gt/gt_communities.json \
  --min_user_interactions 2 \
  --min_users 20 \
  --min_items 20
```

The output JSON contains:
- `meta`: run configuration and dataset stats
- `communities`: list of overlapping communities with `label`, `U`, `V`

## GT sensitivity analysis (try multiple GT thresholds + run r1/r2/r3/r4)

Run one command to sweep `min_user_interactions` for GT construction and evaluate
all four algorithms under fixed `(a,b,sim)` settings:

```bash
python enum/gt_sensitivity_analysis.py \
  --edges data/processed/edges_movielens_small.txt \
  --meta_source local \
  --meta_jsonl data/processed/movielens_meta.jsonl \
  --gt_min_user_interactions 1,2,3,4 \
  --gt_min_users 20 \
  --gt_min_items 20 \
  --ab 40:20,50:25 \
  --sim 0.24,0.26,0.28 \
  --max_iter 20 \
  --ab_step 0 \
  --sim_step 0 \
  --out_csv enum/gt_sensitivity_results.csv
```

- `--ab_step 0` and `--sim_step 0` mean **fixed-parameter iteration** for r3/r4.
- Per setting, output includes: `accuracy`, `precision`, `recall`, `f1`, `jaccard`, `tp/fp/fn/tn`.
- GT files for each threshold are saved under `data/gt/` (default).

## Facebook（人工标注 circles）一步一步流程

> 中文超精简执行清单见：`enum/FACEBOOK_STEP_BY_STEP_CN.md`

如果你选择 SNAP 的第一个 Facebook circles 数据集（人工标注 GT），可以按下面跑：

### Step 1) 下载并解压 Facebook circles

```bash
mkdir -p data/raw/facebook
cd data/raw/facebook
wget https://snap.stanford.edu/data/facebook.tar.gz

# 可用 tar -xzf（大多数环境）
tar -xzf facebook.tar.gz
cd -
```

解压后通常会得到很多 `*.circles` 文件（每个 ego 网络一份）。

### Step 2) 转成本项目可直接运行的二部图 + GT JSON

```bash
python enum/prepare_facebook_circles.py \
  --circles_dir data/raw/facebook/facebook \
  --out_edges data/processed/facebook_circles_bipartite.txt \
  --out_gt data/gt/facebook_circles_gt.json \
  --min_users 5 \
  --include_ego
```

输出说明：
- `data/processed/facebook_circles_bipartite.txt`：`<user_id> <circle_id>` 边。
- `data/gt/facebook_circles_gt.json`：人工 circles 直接形成的 overlapping communities。

### Step 3) 先跑一次单组参数（检查流程）

```bash
python enum/compare_sim_ab_paths.py data/processed/facebook_circles_bipartite.txt 3 3 0.20 jaccard --algo r1
python enum/compare_sim_ab_paths.py data/processed/facebook_circles_bipartite.txt 3 3 0.20 jaccard --algo r2
python enum/compare_sim_ab_paths.py data/processed/facebook_circles_bipartite.txt 3 3 0.20 jaccard --algo r3 --max_iter 20 --ab_step 0
python enum/compare_sim_ab_paths.py data/processed/facebook_circles_bipartite.txt 3 3 0.20 jaccard --algo r4 --max_iter 20 --sim_step 0
```

### Step 4) 跑网格并导出 CSV（论文/汇报常用）

```bash
python enum/run_path_comparison_grid.py \
  --graphs data/processed/facebook_circles_bipartite.txt \
  --sim 0.10,0.15,0.20,0.25,0.30 \
  --ab 2:2,3:3,4:4,5:5 \
  --algos r1,r2,r3,r4 \
  --out_csv enum/facebook_path_compare.csv
```

### Step 5) 画图

```bash
python enum/plot_path_comparison.py enum/facebook_path_compare.csv --out_dir enum/figures_facebook
```

生成的热力图和曲线图可直接放到 PPT / paper appendix。
