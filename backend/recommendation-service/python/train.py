# -*- coding: utf-8 -*-
"""
Wide & Deep 模型训练脚本（论文第3章：数据准备 → 特征工程 → 模型训练）

训练数据来源：user_behaviors 表（MySQL）
特征工程：
  - 用户行为权重：VIEW=1, CLICK=2, ADD_CART=3, PURCHASE=5, RATE=4
  - K-means 聚类：对商品 Embedding 进行聚类，生成 cluster_id
  - 特征输入：(user_id, product_id, category_id, cluster_id, behavior_score)
  - 标签：是否发生 PURCHASE（二分类）
"""

import os
import json
import argparse
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder
from model import WideAndDeepModel

# ─── 行为权重（论文第4章：不同行为赋予不同特征权重）─────────────
BEHAVIOR_WEIGHTS = {
    "VIEW": 1.0,
    "CLICK": 2.0,
    "ADD_CART": 3.0,
    "RATE": 4.0,
    "PURCHASE": 5.0,
}

# ─── 商品类别映射 ─────────────────────────────────────────────────
CATEGORY_MAP = {
    "ELECTRONICS": 1,
    "CLOTHING": 2,
    "HOME_GOODS": 3,
    "BOOKS": 4,
    "SPORTS": 5,
}


class BehaviorDataset(Dataset):
    """用户行为数据集：从 JSON 文件加载（Java 导出）"""

    def __init__(self, data: list[dict], cluster_map: dict[int, int]):
        self.records = []
        for row in data:
            uid = int(row["userId"])
            pid = int(row["productId"])
            cat = CATEGORY_MAP.get(row.get("category", "BOOKS"), 1)
            cluster = cluster_map.get(pid, 0)
            btype = row.get("behaviorType", "VIEW")
            weight = BEHAVIOR_WEIGHTS.get(btype, 1.0)
            # 标签：PURCHASE 为正样本
            label = 1.0 if btype == "PURCHASE" else 0.0
            self.records.append((uid, pid, cat, cluster, weight, label))

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        uid, pid, cat, cluster, score, label = self.records[idx]
        return (
            torch.tensor(uid, dtype=torch.long),
            torch.tensor(pid, dtype=torch.long),
            torch.tensor(cat, dtype=torch.long),
            torch.tensor(cluster, dtype=torch.long),
            torch.tensor(score, dtype=torch.float),
            torch.tensor(label, dtype=torch.float),
        )


def run_kmeans_clustering(
    model: WideAndDeepModel,
    num_products: int,
    n_clusters: int = 10,
) -> dict[int, int]:
    """
    K-means 商品聚类（论文第3章：基于 K-means 的商品聚类）
    使用商品 Embedding 向量作为输入，聚类目标：SSE = Σ Σ ||Qi - μj||²
    返回 {product_id: cluster_id} 映射
    """
    print(f"  执行 K-means 聚类（n_clusters={n_clusters}）...")
    embeddings = []
    for pid in range(1, num_products + 1):
        emb = model.get_product_embedding(pid)
        embeddings.append(emb)

    emb_matrix = np.stack(embeddings)  # (num_products, embedding_dim)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    labels = kmeans.fit_predict(emb_matrix)

    cluster_map = {pid + 1: int(labels[i]) for i, pid in enumerate(range(num_products))}
    print(f"  K-means 完成，SSE={kmeans.inertia_:.2f}")
    return cluster_map


def train(args):
    # ── 加载行为数据 ──────────────────────────────────────────
    print(f"加载数据: {args.data}")
    with open(args.data, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    if not raw_data:
        print("[错误] 数据集为空！请先从数据库导出行为数据。")
        return

    # ── 统计用户/商品数量 ────────────────────────────────────
    user_ids = sorted({int(r["userId"]) for r in raw_data})
    product_ids = sorted({int(r["productId"]) for r in raw_data})
    num_users = max(user_ids)
    num_products = max(product_ids)
    num_categories = len(CATEGORY_MAP)
    num_clusters = args.n_clusters

    print(f"用户数: {len(user_ids)}，商品数: {len(product_ids)}")
    print(f"用户 ID 范围: 1 ~ {num_users}")
    print(f"商品 ID 范围: 1 ~ {num_products}")

    # ── 初始化模型 ───────────────────────────────────────────
    model = WideAndDeepModel(
        num_users=num_users,
        num_products=num_products,
        num_categories=num_categories,
        num_clusters=num_clusters,
        embedding_dim=args.embedding_dim,
        deep_layers=[256, 128, 64],
        dropout=0.3,
    )
    print(f"模型参数量: {sum(p.numel() for p in model.parameters()):,}")

    # ── K-means 聚类（用初始 Embedding）─────────────────────
    print("\n[1/4] K-means 商品聚类...")
    cluster_map = run_kmeans_clustering(model, num_products, num_clusters)

    # ── 构建数据集 ───────────────────────────────────────────
    print("[2/4] 构建数据集...")
    dataset = BehaviorDataset(raw_data, cluster_map)
    val_size = max(1, int(len(dataset) * 0.1))
    train_size = len(dataset) - val_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)
    print(f"  训练集: {train_size} 条，验证集: {val_size} 条")

    # ── 训练 ─────────────────────────────────────────────────
    print("[3/4] 开始训练...")
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-5)
    criterion = nn.BCELoss()
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

    best_val_loss = float("inf")
    for epoch in range(1, args.epochs + 1):
        # 训练
        model.train()
        train_loss = 0.0
        for uid, pid, cat, cluster, score, label in train_loader:
            optimizer.zero_grad()
            pred = model(uid, pid, cat, cluster, score)
            loss = criterion(pred, label)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_loss += loss.item()

        # 验证
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for uid, pid, cat, cluster, score, label in val_loader:
                pred = model(uid, pid, cat, cluster, score)
                val_loss += criterion(pred, label).item()

        train_loss /= len(train_loader)
        val_loss /= max(len(val_loader), 1)
        scheduler.step()

        print(f"  Epoch {epoch:3d}/{args.epochs} | train_loss={train_loss:.4f} | val_loss={val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), args.model_out + ".best.pt")

    # ── 保存最终模型 ─────────────────────────────────────────
    print("[4/4] 保存模型...")
    torch.save(model.state_dict(), args.model_out + ".pt")

    # 保存模型配置（推理时用）
    config = {
        "num_users": num_users,
        "num_products": num_products,
        "num_categories": num_categories,
        "num_clusters": num_clusters,
        "embedding_dim": args.embedding_dim,
        "cluster_map": {str(k): v for k, v in cluster_map.items()},
    }
    with open(args.model_out + ".config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 训练完成！")
    print(f"  最优验证损失: {best_val_loss:.4f}")
    print(f"  模型文件: {args.model_out}.pt")
    print(f"  配置文件: {args.model_out}.config.json")


def main():
    parser = argparse.ArgumentParser(description="Wide & Deep 推荐模型训练")
    parser.add_argument("--data", default="data/behaviors.json", help="行为数据 JSON 文件路径")
    parser.add_argument("--model-out", default="model/wide_deep", help="模型输出路径前缀")
    parser.add_argument("--embedding-dim", type=int, default=32, help="Embedding 维度")
    parser.add_argument("--n-clusters", type=int, default=10, help="K-means 聚类数量")
    parser.add_argument("--epochs", type=int, default=20, help="训练轮数")
    parser.add_argument("--batch-size", type=int, default=256, help="批次大小")
    parser.add_argument("--lr", type=float, default=0.001, help="学习率")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.model_out), exist_ok=True)
    train(args)


if __name__ == "__main__":
    main()
