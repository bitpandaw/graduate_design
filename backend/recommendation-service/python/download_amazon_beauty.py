# -*- coding: utf-8 -*-
"""
下载 Amazon Beauty 数据集（供 SASRec 训练）

数据来源: SNAP Stanford
  - JSON 5-core: reviews_Beauty_5.json.gz (~198k reviews)
  - CSV ratings: ratings_Beauty.csv (~2M ratings)

使用:
  python download_amazon_beauty.py
  python download_amazon_beauty.py --format csv
"""

import argparse
import os
import urllib.request

BASE = "https://snap.stanford.edu/data/amazon/productGraph/categoryFiles"
OUT_DIR = "data"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--format",
        choices=["json", "csv", "both"],
        default="json",
        help="下载格式: json=5-core约198k条 | csv=全量约2M条 | both",
    )
    parser.add_argument("--out-dir", default=OUT_DIR, help="输出目录")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    if args.format in ("json", "both"):
        url = f"{BASE}/reviews_Beauty_5.json.gz"
        out = os.path.join(args.out_dir, "reviews_Beauty_5.json.gz")
        print(f"下载 {url} -> {out}")
        urllib.request.urlretrieve(url, out)
        print("  [OK]")

    if args.format in ("csv", "both"):
        url = f"{BASE}/ratings_Beauty.csv"
        out = os.path.join(args.out_dir, "ratings_Beauty.csv")
        print(f"下载 {url} -> {out}")
        urllib.request.urlretrieve(url, out)
        print("  [OK]")

    print("\n训练示例:")
    if args.format in ("json", "both"):
        print(f"  python train.py --data {args.out_dir}/reviews_Beauty_5.json.gz --dataset amazon_json --epochs 20")
    if args.format in ("csv", "both"):
        print(f"  python train.py --data {args.out_dir}/ratings_Beauty.csv --dataset amazon_csv --epochs 20")


if __name__ == "__main__":
    main()
