"""
SASRec complete training pipeline.
- Local Windows (CPU): python train.py
- Kaggle notebook (GPU): !python train.py  or run cell by cell

Repository structure discovered:
  SASRec.pytorch/python/main.py  model.py  utils.py
  SASRec.pytorch/python/data/    <- Beauty.txt goes here

Known issues fixed:
  1. Repo python/ subdirectory — all paths adjusted
  2. utils.py hardcodes  data/%s.txt  as TWO-column format (uid iid per line)
     -> preprocess() writes one interaction per line, not one sequence per line
  3. Windows multiprocessing requires the train subprocess to be a real child
     -> we call main.py via subprocess (already handles __main__ guard)
  4. utils.py uses n_workers=3 background Process workers; on Windows those
     need the executable to be importable, which subprocess guarantees
  5. num_epochs (not num_epoch) confirmed from source
"""

import os
import sys
import subprocess
import urllib.request

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
REPO_DIR    = os.path.join(BASE_DIR, "SASRec.pytorch")
PYTHON_DIR  = os.path.join(REPO_DIR, "python")          # actual script location
DATA_DIR    = os.path.join(PYTHON_DIR, "data")
RAW_CSV     = os.path.join(BASE_DIR, "ratings_Beauty.csv")
INTER_FILE  = os.path.join(DATA_DIR, "Beauty.txt")

DATASET_URL = (
    "https://snap.stanford.edu/data/amazon/productGraph/"
    "categoryFiles/ratings_Beauty.csv"
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def run(cmd, cwd=None):
    print(f"[RUN] {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    ret = subprocess.run(cmd, shell=isinstance(cmd, str), cwd=cwd)
    if ret.returncode != 0:
        raise RuntimeError(f"Command failed (exit {ret.returncode})")

# ---------------------------------------------------------------------------
# Step 1 — Clone
# ---------------------------------------------------------------------------
def clone_repo():
    if os.path.isdir(REPO_DIR):
        print("[SKIP] Repo already cloned.")
        return
    run(f'git clone https://github.com/pmixer/SASRec.pytorch "{REPO_DIR}"')
    if not os.path.isdir(PYTHON_DIR):
        raise RuntimeError(
            "Cloned repo has unexpected structure — python/ dir not found."
        )

# ---------------------------------------------------------------------------
# Step 2 — Install deps
# ---------------------------------------------------------------------------
def install_deps():
    for pkg in ["torch", "numpy", "tqdm"]:
        run([sys.executable, "-m", "pip", "install", "--quiet", pkg])

# ---------------------------------------------------------------------------
# Step 3 — Download raw CSV
# ---------------------------------------------------------------------------
def download_data():
    if os.path.isfile(RAW_CSV):
        print("[SKIP] ratings_Beauty.csv already exists.")
        return
    print(f"[DOWN] {DATASET_URL}")
    urllib.request.urlretrieve(DATASET_URL, RAW_CSV)
    print(f"[DOWN] Saved → {RAW_CSV}")

# ---------------------------------------------------------------------------
# Step 4 — Preprocess: 5-core filter + write TWO-column Beauty.txt
#
# utils.py data_partition() reads the file line-by-line and does:
#     u, i = line.rstrip().split(' ')   <- expects exactly 2 tokens per line
# build_index() uses np.loadtxt(..., dtype=np.int32) which also needs 2 cols.
#
# So we write one (user_id, item_id) pair per line, sorted by timestamp,
# which is the standard SASRec interaction-list format used by this repo.
# ---------------------------------------------------------------------------
def preprocess():
    if os.path.isfile(INTER_FILE):
        print("[SKIP] Beauty.txt already exists.")
        return

    import csv
    from collections import defaultdict

    print("[PREP] Loading CSV …")
    user_items = defaultdict(list)   # user_raw -> [(ts, item_raw)]
    item_users = defaultdict(set)    # item_raw -> set of user_raw

    with open(RAW_CSV, "r", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 4:
                continue
            user_raw, item_raw, _rating, ts_raw = row[0], row[1], row[2], row[3]
            try:
                ts = int(float(ts_raw))
            except ValueError:
                continue
            user_items[user_raw].append((ts, item_raw))
            item_users[item_raw].add(user_raw)

    # --- 5-core iterative filter ---
    print("[PREP] Applying 5-core filter …")
    while True:
        changed = False

        # drop items < 5 users
        bad_items = {i for i, us in item_users.items() if len(us) < 5}
        if bad_items:
            changed = True
            for u in list(user_items):
                user_items[u] = [(t, i) for t, i in user_items[u]
                                 if i not in bad_items]
                if not user_items[u]:
                    del user_items[u]
            item_users = defaultdict(set)
            for u, seq in user_items.items():
                for _, i in seq:
                    item_users[i].add(u)

        # drop users < 5 items
        bad_users = {u for u, seq in user_items.items() if len(seq) < 5}
        if bad_users:
            changed = True
            for u in bad_users:
                for _, i in user_items[u]:
                    item_users[i].discard(u)
                del user_items[u]

        if not changed:
            break

    print(f"[PREP] After 5-core: {len(user_items)} users, {len(item_users)} items")

    # --- Re-encode 1-indexed ---
    user2id = {u: idx + 1 for idx, u in enumerate(sorted(user_items))}
    item2id = {i: idx + 1 for idx, i in enumerate(sorted(item_users))}

    os.makedirs(DATA_DIR, exist_ok=True)

    # Write ONE PAIR PER LINE: "uid iid\n"  (what utils.py expects)
    print(f"[PREP] Writing {INTER_FILE} …")
    with open(INTER_FILE, "w", encoding="utf-8") as out:
        for u_raw, seq in sorted(user_items.items(),
                                  key=lambda x: user2id[x[0]]):
            uid = user2id[u_raw]
            for ts, i_raw in sorted(seq, key=lambda x: x[0]):
                out.write(f"{uid} {item2id[i_raw]}\n")

    print("[PREP] Done.")

# ---------------------------------------------------------------------------
# Step 5 — Patch repo for known compatibility issues
# ---------------------------------------------------------------------------
def patch_repo():
    """
    Patches applied:
    A) model.py  — no patch needed; already uses torch.bool directly.
    B) utils.py  — Windows: multiprocessing Process is fine when called from
                   a subprocess (our train step), no patch needed.
    C) main.py   — argparse runs at import time (top-level parse_args()).
                   We must pass all required args when calling as subprocess.
                   No code patch needed; handled by our argument list.
    D) utils.py  — data path is hardcoded as 'data/%s.txt' (relative).
                   We run the subprocess with cwd=PYTHON_DIR, so it resolves
                   correctly. No patch needed.
    """
    print("[PATCH] Checking repo for known issues …")

    model_py = os.path.join(PYTHON_DIR, "model.py")
    utils_py = os.path.join(PYTHON_DIR, "utils.py")

    patched_any = False

    # Safety patch: if an older version uses ~torch.tril(...).bool() pattern
    for fpath in [model_py]:
        if not os.path.isfile(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            src = f.read()
        new_src = src.replace(
            "~torch.tril(torch.ones((tl, tl), dtype=torch.bool",
            "~torch.tril(torch.ones((tl, tl), dtype=torch.bool",  # no-op, already correct
        )
        # Older versions sometimes had dtype not set; patch if bool missing
        if "torch.ones((tl, tl))" in new_src and "dtype=torch.bool" not in new_src:
            new_src = new_src.replace(
                "torch.ones((tl, tl))",
                "torch.ones((tl, tl), dtype=torch.bool)"
            )
            patched_any = True
        if new_src != src:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(new_src)

    # utils.py: on Windows, multiprocessing with daemon processes and Queue
    # can fail if the freeze_support() call is missing. Patch main.py instead
    # by ensuring we always call it as a subprocess with __main__ guard active.
    # No file edit needed — subprocess handles this naturally.

    if patched_any:
        print("[PATCH] Applied patches.")
    else:
        print("[PATCH] No patches needed.")

# ---------------------------------------------------------------------------
# Step 6 — Train (subprocess so Windows multiprocessing works correctly)
# ---------------------------------------------------------------------------
def train():
    main_py = os.path.join(PYTHON_DIR, "main.py")
    if not os.path.isfile(main_py):
        raise FileNotFoundError(f"main.py not found: {main_py}")

    # Auto-detect device
    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        device = "cpu"
    print(f"[TRAIN] Device: {device}")

    cmd = [
        sys.executable, "main.py",
        "--dataset",      "Beauty",
        "--train_dir",    "default",
        "--maxlen",       "50",
        "--hidden_units", "64",
        "--num_blocks",   "2",
        "--num_heads",    "2",
        "--dropout_rate", "0.5",
        "--num_epochs",   "50",
        "--batch_size",   "256",
        "--device",       device,
    ]

    # Run from PYTHON_DIR so relative paths (data/Beauty.txt, Beauty_default/)
    # resolve correctly
    run(cmd, cwd=PYTHON_DIR)

    model_dir = os.path.join(PYTHON_DIR, "Beauty_default")
    print(f"\n[DONE] Checkpoints saved under: {model_dir}")
    if os.path.isdir(model_dir):
        files = [f for f in os.listdir(model_dir) if f.endswith(".pth")]
        if files:
            for f in sorted(files):
                print(f"       {os.path.join(model_dir, f)}")

# ---------------------------------------------------------------------------
# Main — MUST be guarded for Windows multiprocessing
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("SASRec training pipeline")
    print("=" * 60)
    clone_repo()
    install_deps()
    download_data()
    preprocess()
    patch_repo()
    train()

if __name__ == "__main__":
    # freeze_support() is required on Windows when using multiprocessing
    # and packaging with PyInstaller; harmless on Linux/Kaggle.
    from multiprocessing import freeze_support
    freeze_support()
    main()
