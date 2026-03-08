# -*- coding: utf-8 -*-
"""
推荐模型
- SASRec: Self-Attentive Sequential Recommendation (Kang & McAuley, 2018)
- WideAndDeepModel: 保留作参考（论文第3章实现）
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


# ─── SASRec 模型 ────────────────────────────────────────────────────


class PointWiseFeedForward(nn.Module):
    """SASRec 中的 point-wise 前馈层"""

    def __init__(self, d: int, d_ff: int, dropout: float = 0.1):
        super().__init__()
        self.linear1 = nn.Linear(d, d_ff)
        self.linear2 = nn.Linear(d_ff, d)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear2(self.dropout(F.gelu(self.linear1(x))))


class SASRecBlock(nn.Module):
    """单层 SASRec Block: Causal Self-Attention + FFN"""

    def __init__(self, d: int, num_heads: int, d_ff: int, dropout: float = 0.1):
        super().__init__()
        self.attn = nn.MultiheadAttention(d, num_heads, dropout=dropout, batch_first=True)
        self.ffn = PointWiseFeedForward(d, d_ff, dropout)
        self.ln1 = nn.LayerNorm(d)
        self.ln2 = nn.LayerNorm(d)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, attn_mask: torch.Tensor | None) -> torch.Tensor:
        # x: (B, L, d)
        attn_out, _ = self.attn(x, x, x, attn_mask=attn_mask, need_weights=False)
        x = self.ln1(x + self.dropout(attn_out))
        x = self.ln2(x + self.dropout(self.ffn(x)))
        return x


class SASRecModel(nn.Module):
    """
    SASRec: Self-Attentive Sequential Recommendation
    给定物品序列 [i_1, ..., i_t]，预测下一个物品 i_{t+1}
    """

    def __init__(
        self,
        num_items: int,
        max_len: int = 50,
        embedding_dim: int = 64,
        num_blocks: int = 2,
        num_heads: int = 2,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.num_items = num_items
        self.max_len = max_len
        self.embedding_dim = embedding_dim
        d_ff = embedding_dim * 4

        self.item_embed = nn.Embedding(num_items + 1, embedding_dim, padding_idx=0)
        self.pos_embed = nn.Embedding(max_len + 1, embedding_dim, padding_idx=0)
        self.blocks = nn.ModuleList(
            [
                SASRecBlock(embedding_dim, num_heads, d_ff, dropout)
                for _ in range(num_blocks)
            ]
        )
        self.dropout = nn.Dropout(dropout)
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Embedding):
                nn.init.xavier_uniform_(m.weight)
                if m.padding_idx is not None:
                    with torch.no_grad():
                        m.weight[m.padding_idx].fill_(0)

    def _causal_mask(self, seq_len: int, device: torch.device) -> torch.Tensor | None:
        """因果掩码：位置 i 只能看到位置 0..i"""
        mask = torch.triu(
            torch.ones(seq_len, seq_len, device=device) * float("-inf"), diagonal=1
        )
        return mask

    def forward(
        self, seq: torch.Tensor, return_all_positions: bool = False
    ) -> torch.Tensor:
        """
        seq: (B, L) 物品 ID 序列，0 为 padding
        return_all_positions: True 返回 (B, L, num_items) 训练用；
                             False 返回 (B, num_items) 推理用（最后一位置）
        """
        B, L = seq.shape
        positions = torch.arange(1, L + 1, device=seq.device, dtype=torch.long)
        positions = positions.unsqueeze(0).expand(B, -1)
        positions = positions.clone()
        positions[seq == 0] = 0  # padding 位置用 0

        x = self.item_embed(seq) + self.pos_embed(positions)
        x = self.dropout(x)

        attn_mask = self._causal_mask(L, seq.device)
        for block in self.blocks:
            x = block(x, attn_mask)

        # x: (B, L, d) -> 与 item_embed 做内积得到 logits
        logits = torch.matmul(x, self.item_embed.weight[1 : self.num_items + 1].T)
        # logits: (B, L, num_items)

        if return_all_positions:
            return logits
        return logits[:, -1, :]  # (B, num_items)


# ─── Wide & Deep 模型（保留作参考）────────────────────────────────────


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
