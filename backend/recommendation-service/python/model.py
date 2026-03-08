# -*- coding: utf-8 -*-
"""
Wide & Deep 推荐模型（论文第3章实现）
- Wide 部分：user_id × category 交叉特征，捕捉记忆能力
- Deep 部分：Embedding → MLP（ReLU 激活），捕捉泛化能力
- 结合矩阵分解预训练的 Embedding + K-means 聚类 ClusterID 特征
"""

import torch
import torch.nn as nn
import numpy as np


class WideAndDeepModel(nn.Module):
    """
    Wide & Deep 混合推荐模型

    Wide 部分（线性）:
        特征交叉：φ_k(x) = ∏ x_i^c_ki, c_ki ∈ {0,1}
        输入：user_id × main_category 交叉向量

    Deep 部分（非线性）:
        Embedding 层 → 拼接 → MLP（ReLU）
        输入：user_id, product_id, cluster_id, 数值特征

    最终输出：sigmoid(wide_out + deep_out)
    """

    def __init__(
        self,
        num_users: int,
        num_products: int,
        num_categories: int,
        num_clusters: int,
        embedding_dim: int = 32,
        deep_layers: list[int] = None,
        dropout: float = 0.3,
    ):
        super().__init__()

        if deep_layers is None:
            deep_layers = [256, 128, 64]

        self.num_users = num_users
        self.num_products = num_products
        self.num_categories = num_categories
        self.num_clusters = num_clusters
        self.embedding_dim = embedding_dim

        # ── Wide 部分 ─────────────────────────────────────────
        # 交叉特征维度 = num_users × num_categories （稀疏交叉积）
        # 实际实现中用 sum(user_embed * category_embed) 近似交叉积
        self.wide_user_embed = nn.Embedding(num_users + 1, embedding_dim, padding_idx=0)
        self.wide_cat_embed = nn.Embedding(num_categories + 1, embedding_dim, padding_idx=0)
        wide_out_dim = 1  # Wide 输出标量

        # ── Deep 部分 Embedding 层 ───────────────────────────
        self.user_embed = nn.Embedding(num_users + 1, embedding_dim, padding_idx=0)
        self.product_embed = nn.Embedding(num_products + 1, embedding_dim, padding_idx=0)
        self.cluster_embed = nn.Embedding(num_clusters + 1, embedding_dim // 2, padding_idx=0)

        # 数值特征：behavior_score (1维)
        num_numerical = 1

        # Deep MLP 输入维度 = user_embed + product_embed + cluster_embed + numerical
        deep_in_dim = embedding_dim + embedding_dim + (embedding_dim // 2) + num_numerical

        # ── Deep MLP 层 ───────────────────────────────────────
        mlp_layers = []
        prev = deep_in_dim
        for hidden in deep_layers:
            mlp_layers.append(nn.Linear(prev, hidden))
            mlp_layers.append(nn.BatchNorm1d(hidden))
            mlp_layers.append(nn.ReLU())
            mlp_layers.append(nn.Dropout(dropout))
            prev = hidden
        mlp_layers.append(nn.Linear(prev, 1))  # Deep 输出标量
        self.deep_mlp = nn.Sequential(*mlp_layers)

        # ── 最终输出 ─────────────────────────────────────────
        self.sigmoid = nn.Sigmoid()

        self._init_weights()

    def _init_weights(self):
        """Xavier 初始化"""
        for m in self.modules():
            if isinstance(m, nn.Embedding):
                nn.init.xavier_uniform_(m.weight)
                if m.padding_idx is not None:
                    with torch.no_grad():
                        m.weight[m.padding_idx].fill_(0)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(
        self,
        user_ids: torch.Tensor,       # (B,)
        product_ids: torch.Tensor,    # (B,)
        category_ids: torch.Tensor,   # (B,)
        cluster_ids: torch.Tensor,    # (B,)
        behavior_scores: torch.Tensor, # (B,)
    ) -> torch.Tensor:
        """前向传播，返回 (B,) 的点击概率"""

        # ── Wide 部分：user × category 交叉积近似 ──────────
        wu = self.wide_user_embed(user_ids)        # (B, D)
        wc = self.wide_cat_embed(category_ids)     # (B, D)
        wide_cross = (wu * wc).sum(dim=-1, keepdim=True)  # (B, 1)

        # ── Deep 部分：Embedding 拼接 → MLP ─────────────────
        pu = self.user_embed(user_ids)             # (B, D)
        pi = self.product_embed(product_ids)       # (B, D)
        pc = self.cluster_embed(cluster_ids)       # (B, D/2)
        bs = behavior_scores.unsqueeze(-1)         # (B, 1)

        deep_input = torch.cat([pu, pi, pc, bs], dim=-1)   # (B, D+D+D/2+1)
        deep_out = self.deep_mlp(deep_input)       # (B, 1)

        # ── Wide + Deep 加权求和 → Sigmoid ───────────────────
        logit = wide_cross + deep_out              # (B, 1)
        return self.sigmoid(logit).squeeze(-1)     # (B,)

    def get_user_embedding(self, user_id: int) -> np.ndarray:
        """获取用户 Embedding 向量（用于矩阵分解可视化）"""
        with torch.no_grad():
            uid = torch.tensor([user_id])
            return self.user_embed(uid).squeeze(0).numpy()

    def get_product_embedding(self, product_id: int) -> np.ndarray:
        """获取商品 Embedding 向量（用于 K-means 聚类输入）"""
        with torch.no_grad():
            pid = torch.tensor([product_id])
            return self.product_embed(pid).squeeze(0).numpy()
