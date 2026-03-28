# -*- coding: utf-8 -*-
"""
SASRec 模型训练脚本

数据源：Amazon Beauty
  - JSON: reviews_Beauty_5.json.gz（5-core，约198k条）
  - CSV:  ratings_Beauty.csv（全量，约2M条）
  下载: python download_amazon_beauty.py
"""

import gzip
import os
import json
import argparse
from collections import defaultdict

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split

from model import SASRecModel


# ─── 数据加载 ────────────────────────────────────────────────────────


def load_amazon_beauty_json(path: str) -> list[tuple[str, str, int]]:
    """
    加载 Amazon Beauty JSON (reviews_Beauty_5.json.gz)
    返回 [(reviewerID, asin, unixReviewTime), ...]
    """
    rows = []
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                try:
                    d = eval(line)
                except Exception:
                    continue
            rid = d.get("reviewerID", "")
            asin = d.get("asin", "")
            ts = int(d.get("unixReviewTime", 0))
            if rid and asin:
                rows.append((rid, asin, ts))
    return rows


def _map_ids_and_build_sequences(
    rows: list[tuple[str, str, int]],
) -> tuple[list[tuple[list[int], int]], int]:
    """
    将原始行映射为整数 ID，构建 (seq, next_item) 样本
    rows: (user_id, item_id, unix_timestamp)
    返回 (samples, num_items)
    """
    user2id = {}
    item2id = {}
    by_user: dict[int, list[tuple[int, int]]] = defaultdict(list)

    for uid_raw, pid_raw, ts in rows:
        uid = user2id.setdefault(uid_raw, len(user2id) + 1)
        pid = item2id.setdefault(pid_raw, len(item2id) + 1)
        by_user[uid].append((pid, ts))

    num_items = len(item2id)
    samples = []
    for uid, events in by_user.items():
        events.sort(key=lambda x: x[1])
        pids = [p for p, _ in events]
        if len(pids) < 2:
            continue
        for t in range(1, len(pids)):
            seq = pids[:t]
            target = pids[t]
            samples.append((seq, target))
    return samples, num_items


def load_data(path: str, dataset: str) -> tuple[list[tuple[list[int], int]], int]:
    """加载 Amazon Beauty 数据，返回 (samples, num_items)"""
    if dataset == "amazon_csv":
        rows = load_amazon_beauty_csv(path)
    else:
        rows = load_amazon_beauty_json(path)
    return _map_ids_and_build_sequences(rows)


class SASRecDataset(Dataset):
    """SASRec 序列数据集：左 padding 到 max_len"""

    def __init__(
        self,
        samples: list[tuple[list[int], int]],
        max_len: int,
        num_items: int,
    ):
        self.samples = []
        for seq, target in samples:
            if target < 1 or target > num_items:
                continue
            padded = [0] * max(0, max_len - len(seq)) + seq[-max_len:]
            self.samples.append((padded, target))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        seq, target = self.samples[idx]
        return (
            torch.tensor(seq, dtype=torch.long),
            torch.tensor(target - 1, dtype=torch.long),  # 0-indexed for CE
        )


def train(args):
    # ── 加载数据 ──────────────────────────────────────────────
    print(f"加载数据: {args.data} (dataset={args.dataset})")
    samples, num_items = load_data(args.data, args.dataset)

    if not samples:
        print("[错误] 数据集为空或无法构建序列。请检查数据格式及路径。")
        return

    print(f"商品数: {num_items}，序列样本数: {len(samples)}")

    # ── 构建序列样本 ──────────────────────────────────────────
    print("\n[1/4] 构建序列样本... [OK]")

    # ── 数据集 ─────────────────────────────────────────────────
    print("[2/4] 构建 DataLoader...")
    dataset = SASRecDataset(samples, args.max_len, num_items)
    val_size = max(1, int(len(dataset) * 0.1))
    train_size = len(dataset) - val_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)
    print(f"  训练集: {train_size} 条，验证集: {val_size} 条")

    # ── 初始化模型 ───────────────────────────────────────────
    model = SASRecModel(
        num_items=num_items,
        max_len=args.max_len,
        embedding_dim=args.embedding_dim,
        num_blocks=args.num_blocks,
        num_heads=args.num_heads,
        dropout=args.dropout,
    )
    print(f"模型参数量: {sum(p.numel() for p in model.parameters()):,}")

    # ── 训练 ─────────────────────────────────────────────────
    print("[3/4] 开始训练...")
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-5)
    criterion = nn.CrossEntropyLoss(ignore_index=-100)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

    best_val_loss = float("inf")
    # 记录每一轮的 loss，方便后续画论文中的训练曲线
    loss_history = []
    for epoch in range(1, args.epochs + 1):
        model.train()
        train_loss = 0.0
        for seq, target in train_loader:
            optimizer.zero_grad()
            logits = model(seq, return_all_positions=True)
            # logits: (B, L, num_items), 取每个序列有效最后位置的预测
            # 简化：用最后一个位置预测（有效序列在右侧）
            logits_last = logits[:, -1, :]
            loss = criterion(logits_last, target)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_loss += loss.item()

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for seq, target in val_loader:
                logits = model(seq, return_all_positions=True)
                logits_last = logits[:, -1, :]
                val_loss += criterion(logits_last, target).item()

        train_loss /= len(train_loader)
        val_loss /= max(len(val_loader), 1)
        scheduler.step()

        print(
            f"  Epoch {epoch:3d}/{args.epochs} | train_loss={train_loss:.4f} | val_loss={val_loss:.4f}"
        )

        # 追加到内存中的历史，训练结束一次性写入文件
        loss_history.append(
            {
                "epoch": epoch,
                "train_loss": float(train_loss),
                "val_loss": float(val_loss),
            }
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), args.model_out + ".best.pt")

    # ── 保存模型与配置 ───────────────────────────────────────
    print("[4/4] 保存模型与训练日志...")
    torch.save(model.state_dict(), args.model_out + ".pt")

    config = {
        "num_items": num_items,
        "max_len": args.max_len,
        "embedding_dim": args.embedding_dim,
        "num_blocks": args.num_blocks,
        "num_heads": args.num_heads,
        "dropout": args.dropout,
    }
    with open(args.model_out + ".config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    # 保存每一轮训练/验证损失，供 generate_thesis_charts.py 使用真实数据画图
    loss_log_path = args.model_out + ".loss_history.json"
    try:
        with open(loss_log_path, "w", encoding="utf-8") as f:
            json.dump(loss_history, f, ensure_ascii=False, indent=2)
        print(f"  训练损失日志: {loss_log_path}")
    except Exception as e:
        print(f"[警告] 无法写入训练损失日志 {loss_log_path}: {e}")

    print("\n[OK] 训练完成!")
    print(f"  最优验证损失: {best_val_loss:.4f}")
    print(f"  模型文件: {args.model_out}.pt")
    print(f"  配置文件: {args.model_out}.config.json")


def main():
    parser = argparse.ArgumentParser(description="SASRec 推荐模型训练")
    parser.add_argument(
        "--data",
        default="data/reviews_Beauty_5.json.gz",
        help="Amazon Beauty 数据路径（JSON/GZ 或 CSV）",
    )
    parser.add_argument(
        "--dataset",
        choices=["amazon_json", "amazon_csv"],
        default="amazon_json",
        help="格式: amazon_json=JSON 5-core | amazon_csv=CSV 全量",
    )
    parser.add_argument("--model-out", default="model/sasrec", help="模型输出路径前缀")
    parser.add_argument("--max-len", type=int, default=50, help="最大序列长度")
    parser.add_argument("--embedding-dim", type=int, default=64, help="Embedding 维度")
    parser.add_argument("--num-blocks", type=int, default=2, help="Transformer 层数")
    parser.add_argument("--num-heads", type=int, default=2, help="注意力头数")
    parser.add_argument("--dropout", type=float, default=0.1, help="Dropout")
    parser.add_argument("--epochs", type=int, default=20, help="训练轮数")
    parser.add_argument("--batch-size", type=int, default=256, help="批次大小")
    parser.add_argument("--lr", type=float, default=0.001, help="学习率")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.model_out) or ".", exist_ok=True)
    train(args)


if __name__ == "__main__":
    main()
