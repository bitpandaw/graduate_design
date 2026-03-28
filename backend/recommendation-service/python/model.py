# -*- coding: utf-8 -*-
"""
推荐模型
- SASRec: Self-Attentive Sequential Recommendation (Kang & McAuley, 2018)
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



