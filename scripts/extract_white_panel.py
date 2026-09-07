#!/usr/bin/env python3
"""从黑底商品浏览截图中提取中央的大面积近白商品图区域。

用法:
  python extract_white_panel.py INPUT OUTPUT [TOP_TRIM] [MIN_WHITE_RATIO]
默认顶部额外去掉80px，用于去除商品图区域上方品牌/标题文字。
如果检测失败则以原图为输出，并返回非零退出码，避免静默产生错误裁剪。
"""
import sys
from pathlib import Path
from PIL import Image
import numpy as np


def detect_panel(img, min_white_ratio=0.55):
    arr = np.asarray(img.convert("RGB")).astype("int16")
    white = np.all(arr >= 235, axis=2)
    row_ratio = white.mean(axis=1)
    col_ratio = white.mean(axis=0)
    h, w = white.shape

    rows = np.where(row_ratio >= min_white_ratio)[0]
    cols = np.where(col_ratio >= min_white_ratio)[0]
    if len(rows) < max(20, h * 0.15) or len(cols) < max(20, w * 0.15):
        return None

    # 取连续跨度最大的候选区，而不是单个UI图标。
    def largest_run(values):
        best = None
        start = prev = int(values[0])
        for v in values[1:]:
            v = int(v)
            if v == prev + 1:
                prev = v
            else:
                cand = (start, prev + 1)
                if best is None or cand[1] - cand[0] > best[1] - best[0]:
                    best = cand
                start = prev = v
        cand = (start, prev + 1)
        if best is None or cand[1] - cand[0] > best[1] - best[0]:
            best = cand
        return best

    rr = largest_run(rows)
    cc = largest_run(cols)
    if not rr or not cc:
        return None
    x0, x1 = cc
    y0, y1 = rr
    if (x1 - x0) * (y1 - y0) < 0.15 * w * h:
        return None
    return x0, y0, x1, y1


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    inp, out = sys.argv[1:3]
    trim = int(sys.argv[3]) if len(sys.argv) >= 4 else 80
    ratio = float(sys.argv[4]) if len(sys.argv) >= 5 else 0.55
    img = Image.open(inp).convert("RGB")
    bbox = detect_panel(img, ratio)
    if not bbox:
        print("[失败] 未可靠检测到大面积白色商品图区域；保留原图，不执行猜测性裁剪")
        img.save(out, quality=95)
        return 1
    x0, y0, x1, y1 = bbox
    y0 = min(y1 - 1, y0 + max(0, trim))
    cropped = img.crop((x0, y0, x1, y1))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    cropped.save(out, quality=95)
    print(f"[white-panel] 输出: {out}; bbox={bbox}; top_trim={trim}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
