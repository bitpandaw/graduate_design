import os
import shutil
import subprocess
from pathlib import Path


def run_cmd(cmd, cwd):
    print(f"\n[RUN] {cmd} (cwd={cwd})")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        shell=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"命令执行失败: {cmd} (code={result.returncode})")


def main():
    repo_root = Path(__file__).resolve().parent

    rec_py_dir = repo_root / "backend" / "recommendation-service" / "python"

    # 1. 始终重新训练模型，保证训练曲线基于最新一次训练
    print("[STEP 1] 重新训练 SASRec 模型，用于生成真实训练曲线...")
    run_cmd("python train.py", cwd=str(rec_py_dir))

    # 2. 始终重新评估一次，保证 HR/NDCG 指标与当前模型一致
    print("[STEP 2] 重新执行离线评估，生成最新 HR/NDCG 指标...")
    run_cmd("python evaluate.py", cwd=str(rec_py_dir))

    # 3. 始终重新进行一次网关压测，生成最新压测结果
    backend_dir = repo_root / "backend"
    print("[STEP 3] 重新执行网关压测，生成最新 QPS/延迟数据...")
    run_cmd("python stress_test.py", cwd=str(backend_dir))

    # 4. 统一基于最新数据生成论文中 5.2 / 5.3 的图表
    run_cmd("python generate_thesis_charts.py", cwd=str(repo_root))

    # 5. 收集并拷贝所有相关图片到 picture 目录
    picture_dir = repo_root / "picture"
    picture_dir.mkdir(exist_ok=True)

    png_paths: list[Path] = []

    # 5.1 论文图表目录
    thesis_dir = repo_root / "thesis_charts"
    if thesis_dir.exists():
        png_paths.extend(thesis_dir.glob("*.png"))

    # 5.2 网关压测图
    gateway_png = backend_dir / "gateway_stress_test.png"
    if gateway_png.exists():
        png_paths.append(gateway_png)

    # 5.3 推荐评估脚本生成的图
    rec_png1 = rec_py_dir / "sasrec_metrics_by_k.png"
    rec_png2 = rec_py_dir / "model_comparison.png"
    for p in (rec_png1, rec_png2):
        if p.exists():
            png_paths.append(p)

    print("\n[INFO] 准备拷贝以下图片到 picture 目录：")
    for src in png_paths:
        dst = picture_dir / src.name
        print(f"  {src} -> {dst}")
        shutil.copy2(src, dst)

    print(f"\n全部流程完成。最终图片已汇总到: {picture_dir}")


if __name__ == "__main__":
    main()

