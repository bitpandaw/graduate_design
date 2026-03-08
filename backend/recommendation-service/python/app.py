# -*- coding: utf-8 -*-
"""
SASRec 推荐服务 FastAPI

接口：
  GET  /health                           健康检查
  POST /recommend                        获取推荐商品 ID 列表（含分数）
  POST /behavior/score                   序列 + 候选商品的 next-item 概率
  GET  /model/info                       模型配置信息

Java RecommendationEngine 通过 HTTP 调用本服务。
推荐响应时延目标：< 200ms
"""

import json
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

import torch
import torch.nn.functional as F
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from model import SASRecModel

# ─── 常量 ────────────────────────────────────────────────────────
MODEL_DIR = os.environ.get("MODEL_DIR", "model")
CONFIG_PATH = os.path.join(MODEL_DIR, "sasrec.config.json")
MODEL_PATH = os.path.join(MODEL_DIR, "sasrec.best.pt")

# ─── 全局状态 ─────────────────────────────────────────────────────
_model: Optional[SASRecModel] = None
_config: Optional[dict] = None


def load_model():
    global _model, _config

    if not os.path.exists(CONFIG_PATH):
        print(f"[警告] 模型配置不存在: {CONFIG_PATH}，将使用默认冷启动配置")
        _config = {
            "num_items": 500,
            "max_len": 50,
            "embedding_dim": 64,
            "num_blocks": 2,
            "num_heads": 2,
            "dropout": 0.1,
        }
    else:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _config = json.load(f)

    _model = SASRecModel(
        num_items=_config["num_items"],
        max_len=_config["max_len"],
        embedding_dim=_config.get("embedding_dim", 64),
        num_blocks=_config.get("num_blocks", 2),
        num_heads=_config.get("num_heads", 2),
        dropout=_config.get("dropout", 0.1),
    )

    if os.path.exists(MODEL_PATH):
        _model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
        print(f"[OK] 已加载训练模型: {MODEL_PATH}")
    else:
        print(f"[信息] 未找到训练权重 {MODEL_PATH}，使用随机初始化（冷启动模式）")

    _model.eval()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("启动推荐服务，加载 SASRec 模型...")
    load_model()
    yield
    print("推荐服务关闭")


app = FastAPI(
    title="SASRec 推荐服务",
    description="基于 SASRec 序列推荐的个性化推荐 API",
    version="1.0.0",
    lifespan=lifespan,
)


# ─── 请求/响应模型 ────────────────────────────────────────────────
class RecommendRequest(BaseModel):
    userId: int
    candidateProductIds: list[int]
    recentItemIds: Optional[list[int]] = None  # 用户最近行为序列，按时间升序
    limit: int = 10


class ProductScore(BaseModel):
    productId: int
    score: float


class RecommendResponse(BaseModel):
    userId: int
    recommendations: list[ProductScore]
    latencyMs: float
    modelMode: str


class BehaviorScoreRequest(BaseModel):
    recentItemIds: list[int]
    productId: int


# ─── 工具函数 ─────────────────────────────────────────────────────
def _build_seq(recent: list[int], max_len: int) -> torch.Tensor:
    """构建输入序列，左 padding 到 max_len"""
    seq = (recent or [])[-max_len:]
    padded = [0] * max(0, max_len - len(seq)) + seq
    return torch.tensor([padded], dtype=torch.long)


def _predict_scores_sasrec(
    recent_item_ids: list[int],
    candidate_product_ids: list[int],
) -> list[float]:
    """基于 SASRec 对候选商品打分（next-item logits 转为概率）"""
    if _model is None:
        return [0.5] * len(candidate_product_ids)

    max_len = _config["max_len"]
    num_items = _config["num_items"]

    seq = _build_seq(recent_item_ids, max_len)

    with torch.no_grad():
        logits = _model(seq, return_all_positions=False)
    # logits: (1, num_items)，索引 i 对应物品 i+1
    logits = logits.squeeze(0)

    scores = []
    for pid in candidate_product_ids:
        if 1 <= pid <= num_items:
            s = logits[pid - 1].item()
            scores.append(s)
        else:
            scores.append(float("-inf"))

    # 转为 softmax 概率便于展示；排序只关心相对大小
    all_scores = torch.tensor(scores, dtype=torch.float32)
    probs = F.softmax(all_scores, dim=0)
    return probs.tolist()


# ─── API 接口 ─────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": _model is not None,
        "model_mode": "trained" if os.path.exists(MODEL_PATH) else "cold_start",
    }


@app.get("/model/info")
def model_info():
    if _config is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    return {
        "config": _config,
        "model_file": MODEL_PATH,
        "model_exists": os.path.exists(MODEL_PATH),
    }


@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    """
    核心推荐接口：给定用户最近行为序列，对候选商品打分，按分数降序返回 TopK
    冷启动（recentItemIds 为空）：返回均匀分数
    """
    t0 = time.perf_counter()

    if not req.candidateProductIds:
        raise HTTPException(status_code=400, detail="candidateProductIds 不能为空")

    recent = req.recentItemIds or []

    if not recent:
        scores = [0.5] * len(req.candidateProductIds)
    else:
        scores = _predict_scores_sasrec(recent, req.candidateProductIds)

    scored = sorted(
        zip(req.candidateProductIds, scores),
        key=lambda x: x[1],
        reverse=True,
    )
    top_k = scored[: req.limit]
    latency_ms = (time.perf_counter() - t0) * 1000

    return RecommendResponse(
        userId=req.userId,
        recommendations=[ProductScore(productId=pid, score=round(s, 4)) for pid, s in top_k],
        latencyMs=round(latency_ms, 2),
        modelMode="trained" if os.path.exists(MODEL_PATH) else "cold_start",
    )


@app.post("/behavior/score")
def behavior_score(req: BehaviorScoreRequest):
    """给定序列 + 单个候选商品，返回 next-item 概率（调试用）"""
    scores = _predict_scores_sasrec(req.recentItemIds, [req.productId])
    return {
        "recentItemIds": req.recentItemIds,
        "productId": req.productId,
        "score": round(scores[0], 4),
        "modelMode": "trained" if os.path.exists(MODEL_PATH) else "cold_start",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090, log_level="info")
