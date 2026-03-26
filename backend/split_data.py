"""
Split codesearchnet_test.jsonl into train/test sets (80/20).
Run once before fine-tuning.
"""
import json
import random
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
INPUT_FILE  = "data/evaluation/codesearchnet_test.jsonl"
TRAIN_FILE  = "data/evaluation/train.jsonl"
TEST_FILE   = "data/evaluation/test.jsonl"
SPLIT_RATIO = 0.8   # 80% train, 20% test
RANDOM_SEED = 42    # for reproducibility
# ─────────────────────────────────────────────────────────────────────────────

# Load all samples
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    all_samples = [json.loads(line) for line in f if line.strip()]

print(f"Total samples loaded: {len(all_samples)}")

# Shuffle with fixed seed so results are reproducible
random.seed(RANDOM_SEED)
random.shuffle(all_samples)

# Split
split_idx     = int(len(all_samples) * SPLIT_RATIO)
train_samples = all_samples[:split_idx]
test_samples  = all_samples[split_idx:]

# Save
Path(TRAIN_FILE).parent.mkdir(parents=True, exist_ok=True)

with open(TRAIN_FILE, "w", encoding="utf-8") as f:
    for s in train_samples:
        f.write(json.dumps(s) + "\n")

with open(TEST_FILE, "w", encoding="utf-8") as f:
    for s in test_samples:
        f.write(json.dumps(s) + "\n")

print(f"Train set: {len(train_samples)} samples → {TRAIN_FILE}")
print(f"Test set:  {len(test_samples)} samples  → {TEST_FILE}")
print(f"\nDone! Now update finetune.py to use: {TRAIN_FILE}")
print(f"And evaluate against:               {TEST_FILE}")