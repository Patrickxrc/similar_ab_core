# 你现在的下一步（建议按这个顺序）

```bash
# 1) 先确认 CSV 已生成
ls -lh enum/facebook_path_compare.csv

# 2) 如果本机没装 matplotlib，先装（WSL 常见）
python -m pip install --user matplotlib

# 3) 重新画图（脚本已支持 algo-grid CSV）
python enum/plot_path_comparison.py enum/facebook_path_compare.csv --out_dir enum/figures_facebook

# 4) 检查图是否生成
ls -lh enum/figures_facebook

# 5) 如需快速看结果，打开 edge_jaccard 热力图
# (WSL + Windows)
explorer.exe enum/figures_facebook
```

## 如果第 3 步还报错

```bash
# 看 CSV 头，确认列名
python - <<'PY'
import csv
with open('enum/facebook_path_compare.csv', newline='') as f:
    r = csv.reader(f)
    print(next(r))
PY

# 看前 5 行
python - <<'PY'
import csv
from itertools import islice
with open('enum/facebook_path_compare.csv', newline='') as f:
    r = csv.DictReader(f)
    for row in islice(r, 5):
        print(row)
PY
```
