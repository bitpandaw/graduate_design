# -*- coding: utf-8 -*-
"""
Wide & Deep 推荐服务 FastAPI（论文第4章：推荐服务模块实现）

接口：
  GET  /health                           健康检查
  POST /recommend                        获取推荐商品 ID 列表（含分数）
  POST /behavior/score                   单条行为特征预测
  GET  /model/info                       模型配置信息

Java RecommendationEngine 通过 HTTP 调用本服务。
推荐响应时延目标：< 200ms（论文第4章非功能性需求）
"""

import json
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from model import WideAndDeepModel

# ─── 常量 ────────────────────────────────────────────────────────
MODEL_DIR = os.environ.get("MODEL_DIR", "model")
CONFIG_PATH = os.path.join(MODEL_DIR, "wide_deep.config.json")
MODEL_PATH = os.path.join(MODEL_DIR, "wide_deep.best.pt")

CATEGORY_MAP = {
    "ELECTRONICS": 1,
    "CLOTHING": 2,
    "HOME_GOODS": 3,
    "BOOKS": 4,
    "SPORTS": 5,
}

BEHAVIOR_WEIGHTS = {
    "VIEW": 1.0,
    "CLICK": 2.0,
    "ADD_CART": 3.0,
    "RATE": 4.0,
    "PURCHASE": 5.0,
}

# ─── 全局状态 ─────────────────────────────────────────────────────
_model: Optional[WideAndDeepModel] = None
_config: Optional[dict] = None
_cluster_map: Optional[dict] = None


def load_model():
    global _model, _config, _cluster_map

    if not os.path.exists(CONFIG_PATH):
        print(f"[警告] 模型配置不存在: {CONFIG_PATH}，将使用默认冷启动配置")
        # 冷启动：使用默认参数（未训练）
        _config = {
            "num_users": 1000,
            "num_products": 500,
            "num_categories": 5,
            "num_clusters": 10,
            "embedding_dim": 32,
            "cluster_map": {},
        }
    else:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _config = json.load(f)

    _cluster_map = {int(k): v for k, v in _config.get("cluster_map", {}).items()}

    _model = WideAndDeepModel(
        num_users=_config["num_users"],
        num_products=_config["num_products"],
        num_categories=_config["num_categories"],
        num_clusters=_config["num_clusters"],
        embedding_dim=_config.get("embedding_dim", 32),
    )

    if os.path.exists(MODEL_PATH):
        _model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
        print(f"✅ 已加载训练模型: {MODEL_PATH}")
    else:
        print(f"[信息] 未找到训练权重 {MODEL_PATH}，使用随机初始化（冷启动模式）")

    _model.eval()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("启动推荐服务，加载 Wide & Deep 模型...")
    load_model()
    yield
    print("推荐服务关闭")


app = FastAPI(
    title="Wide & Deep 推荐服务",
    description="基于 Wide & Deep 模型的个性化推荐 API（论文第3-4章实现）",
    version="1.0.0",
    lifespan=lifespan,
)


# ─── 请求/响应模型 ────────────────────────────────────────────────
class RecommendRequest(BaseModel):
    userId: int
    candidateProductIds: list[int]       # 候选商品 ID 列表（由 Java 传入）
    categoryHint: Optional[str] = None  # 用户最近偏好类别（可选）
    limit: int = 10


class ProductScore(BaseModel):
    productId: int
    score: float


class RecommendResponse(BaseModel):
    userId: int
    recommendations: list[ProductScore]  # 按 score 降序排列
    latencyMs: float
    modelMode: str                        # "trained" 或 "cold_start"


class BehaviorScoreRequest(BaseModel):
    userId: int
    productId: int
    categoryId: int
    behaviorType: str = "VIEW"


# ─── 工具函数 ─────────────────────────────────────────────────────
def _clamp_id(val: int, max_val: int) -> int:
    """将 ID clamp 到模型范围内，超出的用 0（padding）"""
    return val if 1 <= val <= max_val else 0


def _predict_scores(
    user_id: int,
    product_ids: list[int],
    category_id: int,
    behavior_score: float,
) -> list[float]:
    """批量预测用户对商品列表的偏好分数"""
    if _model is None:
        return [0.5] * len(product_ids)

    n = len(product_ids)
    uid_clamped = _clamp_id(user_id, _config["num_users"])
    cat_clamped = min(max(category_id, 1), _config["num_categories"])

    uid_t = torch.tensor([uid_clamped] * n, dtype=torch.long)
    pid_t = torch.tensor(
        [_clamp_id(p, _config["num_products"]) for p in product_ids],
        dtype=torch.long,
    )
    cat_t = torch.tensor([cat_clamped] * n, dtype=torch.long)
    cluster_t = torch.tensor(
        [_cluster_map.get(p, 0) for p in product_ids],
        dtype=torch.long,
    )
    score_t = torch.tensor([behavior_score] * n, dtype=torch.float)

    with torch.no_grad():
        probs = _model(uid_t, pid_t, cat_t, cluster_t, score_t)  # (n,)
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
        "config": {k: v for k, v in _config.items() if k != "cluster_map"},
        "model_file": MODEL_PATH,
        "model_exists": os.path.exists(MODEL_PATH),
        "cluster_count": len(_cluster_map) if _cluster_map else 0,
    }


@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    """
    核心推荐接口：对候选商品列表打分，按分数降序返回 TopK

    论文非功能需求：Wide & Deep 推理 < 200ms
    """
    t0 = time.perf_counter()

    if not req.candidateProductIds:
        raise HTTPException(status_code=400, detail="candidateProductIds 不能为空")

    # 确定类别 ID
    category_id = CATEGORY_MAP.get(req.categoryHint or "", 1)

    # 推理
    scores = _predict_scores(
        user_id=req.userId,
        product_ids=req.candidateProductIds,
        category_id=category_id,
        behavior_score=BEHAVIOR_WEIGHTS.get("VIEW", 1.0),
    )

    # 组合并排序
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
    """预测单条行为的偏好分数（用于调试）"""
    behavior_w = BEHAVIOR_WEIGHTS.get(req.behaviorType, 1.0)
    scores = _predict_scores(
        user_id=req.userId,
        product_ids=[req.productId],
        category_id=req.categoryId,
        behavior_score=behavior_w,
    )
    return {
        "userId": req.userId,
        "productId": req.productId,
        "score": round(scores[0], 4),
        "behaviorType": req.behaviorType,
        "modelMode": "trained" if os.path.exists(MODEL_PATH) else "cold_start",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090, log_level="info")
