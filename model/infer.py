"""
SASRec 推理示例
用法: python infer.py
"""

import sys
import os
import numpy as np
import torch

# 把 SASRec 的 python 目录加入路径
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PYTHON_DIR = os.path.join(BASE_DIR, "SASRec.pytorch", "python")
sys.path.insert(0, PYTHON_DIR)

from model import SASRec

# ---------------------------------------------------------------------------
# 超参数 —— 必须与训练时一致
# ---------------------------------------------------------------------------
MAXLEN       = 50
HIDDEN_UNITS = 64
NUM_BLOCKS   = 2
NUM_HEADS    = 2
DROPOUT_RATE = 0.5
DEVICE       = "cpu"

# 从 Beauty.txt 读取 usernum / itemnum
DATA_FILE  = os.path.join(PYTHON_DIR, "data", "Beauty.txt")
MODEL_PATH = os.path.join(PYTHON_DIR, "Beauty_default",
    "SASRec.epoch=40.lr=0.001.layer=2.head=2.hidden=64.maxlen=50.pth")

# ---------------------------------------------------------------------------
# 读取数据，得到 usernum / itemnum 以及用户历史
# ---------------------------------------------------------------------------
def load_data(path):
    user_items = {}
    with open(path, "r") as f:
        for line in f:
            u, i = line.strip().split()
            u, i = int(u), int(i)
            user_items.setdefault(u, []).append(i)
    usernum = max(user_items.keys())
    itemnum = max(i for seq in user_items.values() for i in seq)
    return user_items, usernum, itemnum

# ---------------------------------------------------------------------------
# 把用户历史截断 / 左填充到 maxlen
# ---------------------------------------------------------------------------
def make_seq(history, maxlen):
    seq = np.zeros(maxlen, dtype=np.int32)
    idx = maxlen - 1
    for item in reversed(history[-maxlen:]):
        seq[idx] = item
        idx -= 1
    return seq  # shape: (maxlen,)

# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main():
    print("[INFO] 加载数据 ...")
    user_items, usernum, itemnum = load_data(DATA_FILE)
    print(f"[INFO] usernum={usernum}, itemnum={itemnum}")

    # 构建模型
    class Args:
        device       = DEVICE
        hidden_units = HIDDEN_UNITS
        maxlen       = MAXLEN
        num_blocks   = NUM_BLOCKS
        num_heads    = NUM_HEADS
        dropout_rate = DROPOUT_RATE
        norm_first   = False

    model = SASRec(usernum, itemnum, Args()).to(DEVICE)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()
    print(f"[INFO] 模型加载完毕: {MODEL_PATH}")

    # -----------------------------------------------------------------------
    # 示例：为用户 1 推荐 Top-10
    # -----------------------------------------------------------------------
    target_user = 1
    history = user_items.get(target_user, [])
    print(f"\n[用户 {target_user}] 历史交互 ({len(history)} 条): {history[:10]} ...")

    # 序列输入: shape (1, maxlen)
    seq = make_seq(history, MAXLEN)[np.newaxis, :]  # (1, 50)

    # 候选物品: 所有物品（排除历史已交互）
    seen = set(history)
    candidates = [i for i in range(1, itemnum + 1) if i not in seen]

    with torch.no_grad():
        # logits shape: (1, len(candidates))
        logits = model.predict(
            user_ids    = np.array([target_user]),
            log_seqs    = seq,
            item_indices= np.array(candidates)
        )

    scores = logits[0].cpu().numpy()  # (num_candidates,)
    top10_idx = np.argsort(scores)[::-1][:10]
    top10_items = [candidates[i] for i in top10_idx]

    print(f"\n[用户 {target_user}] Top-10 推荐物品 ID:")
    for rank, item_id in enumerate(top10_items, 1):
        print(f"  #{rank:2d}  item_id={item_id}  score={scores[top10_idx[rank-1]]:.4f}")

if __name__ == "__main__":
    main()
