# Facebook（SNAP circles）从零到出图：一步一步

> 适用时间：2026-03-22 当前仓库版本。
> 目标：使用 **人工标注 circles** 做 GT，并跑出 r1/r2/r3/r4 对比结果与图。

> 只要命令版：`enum/FACEBOOK_COMMANDS_ONLY.md`

## 0) 先确认你在仓库根目录

```bash
cd /workspace/similar_ab_core
pwd
```

## 1) 下载 Facebook circles 数据

```bash
mkdir -p data/raw/facebook
cd data/raw/facebook
wget https://snap.stanford.edu/data/facebook.tar.gz
tar -xzf facebook.tar.gz
cd /workspace/similar_ab_core
```

下载完成后，目录 `data/raw/facebook/facebook/` 下应有大量 `*.circles` 文件。

## 2) 转换为本项目可运行格式（二部图 + GT）

```bash
python enum/prepare_facebook_circles.py \
  --circles_dir data/raw/facebook/facebook \
  --out_edges data/processed/facebook_circles_bipartite.txt \
  --out_gt data/gt/facebook_circles_gt.json \
  --min_users 5 \
  --include_ego
```

你会得到：
- `data/processed/facebook_circles_bipartite.txt`（`user_id circle_id`）
- `data/gt/facebook_circles_gt.json`（人工 circles 形成的 overlapping GT）

## 3) 先做一次最小验证（四个算法各跑一次）

```bash
python enum/compare_sim_ab_paths.py data/processed/facebook_circles_bipartite.txt 3 3 0.20 jaccard --algo r1
python enum/compare_sim_ab_paths.py data/processed/facebook_circles_bipartite.txt 3 3 0.20 jaccard --algo r2
python enum/compare_sim_ab_paths.py data/processed/facebook_circles_bipartite.txt 3 3 0.20 jaccard --algo r3 --max_iter 20 --ab_step 0
python enum/compare_sim_ab_paths.py data/processed/facebook_circles_bipartite.txt 3 3 0.20 jaccard --algo r4 --max_iter 20 --sim_step 0
```

如果四条都正常输出 JSON，说明流程打通。

这里建议 `--ab_step 0` 和 `--sim_step 0`，表示 r3/r4 迭代时参数固定不变，只做结构收敛，便于和 r1/r2 公平对比。

## 4) 跑参数网格（生成汇总 CSV）

```bash
python enum/run_path_comparison_grid.py \
  --graphs data/processed/facebook_circles_bipartite.txt \
  --sim 0.10,0.15,0.20,0.25,0.30 \
  --ab 2:2,3:3,4:4,5:5 \
  --algos r1,r2,r3,r4 \
  --out_csv enum/facebook_path_compare.csv
```

输出文件：`enum/facebook_path_compare.csv`

## 5) 一键画图（PPT 可直接用）

```bash
python enum/plot_path_comparison.py enum/facebook_path_compare.csv --out_dir enum/figures_facebook
```

输出目录：`enum/figures_facebook/`，包含热力图与曲线图。

## 6) 建议的“第一次汇报”参数

如果你只想先出一版稳定结果：
- `sim`: `0.15,0.20,0.25`
- `(a,b)`: `2:2,3:3,4:4`
- `algos`: `r1,r2,r3,r4`

这样计算量小，图也够说明问题。
