# Facebook circles 命令清单（无 Step 说明）

> 跑完后建议继续：`enum/NEXT_ACTIONS_CN.md`

> 默认采用固定参数迭代：`--ab_step 0`、`--sim_step 0`。

```bash
cd /workspace/similar_ab_core
pwd

mkdir -p data/raw/facebook
cd data/raw/facebook
wget https://snap.stanford.edu/data/facebook.tar.gz
tar -xzf facebook.tar.gz
cd /workspace/similar_ab_core

python enum/prepare_facebook_circles.py \
  --circles_dir data/raw/facebook/facebook \
  --out_edges data/processed/facebook_circles_bipartite.txt \
  --out_gt data/gt/facebook_circles_gt.json \
  --min_users 5 \
  --include_ego

python enum/compare_sim_ab_paths.py data/processed/facebook_circles_bipartite.txt 3 3 0.20 jaccard --algo r1
python enum/compare_sim_ab_paths.py data/processed/facebook_circles_bipartite.txt 3 3 0.20 jaccard --algo r2
python enum/compare_sim_ab_paths.py data/processed/facebook_circles_bipartite.txt 3 3 0.20 jaccard --algo r3 --max_iter 20 --ab_step 0
python enum/compare_sim_ab_paths.py data/processed/facebook_circles_bipartite.txt 3 3 0.20 jaccard --algo r4 --max_iter 20 --sim_step 0

# r3/r4 之后的后续命令
python enum/run_path_comparison_grid.py \
  --graphs data/processed/facebook_circles_bipartite.txt \
  --sim 0.10,0.15,0.20,0.25,0.30 \
  --ab 2:2,3:3,4:4,5:5 \
  --algos r1,r2,r3,r4 \
  --out_csv enum/facebook_path_compare.csv

python enum/plot_path_comparison.py enum/facebook_path_compare.csv --out_dir enum/figures_facebook

ls data/processed/facebook_circles_bipartite.txt
ls data/gt/facebook_circles_gt.json
ls enum/facebook_path_compare.csv
ls enum/figures_facebook
```
