"""
Download official CodeSearchNet train/test splits from HuggingFace.
Fine-tune on train split, evaluate on official test split.
"""
from datasets import load_dataset
import json
from pathlib import Path

Path("data/evaluation").mkdir(parents=True, exist_ok=True)

print("Downloading CodeSearchNet Python split...")
dataset = load_dataset("code_search_net", "python", trust_remote_code=True)

# Save training split (use 500 samples — manageable on CPU)
train_samples = []
for sample in dataset["train"]:
    code = sample.get("whole_func_string", "")
    doc  = sample.get("func_documentation_string", "")
    if code and doc:
        train_samples.append({
            "code": code,
            "doc":  doc,
            "language": "python"
        })
    if len(train_samples) >= 500:
        break

with open("data/evaluation/csn_train.jsonl", "w") as f:
    for s in train_samples:
        f.write(json.dumps(s) + "\n")

# Save official test split (use 200 samples)
test_samples = []
for sample in dataset["test"]:
    code = sample.get("whole_func_string", "")
    doc  = sample.get("func_documentation_string", "")
    if code and doc:
        test_samples.append({
            "code": code,
            "doc":  doc,
            "language": "python"
        })
    if len(test_samples) >= 200:
        break

with open("data/evaluation/csn_test.jsonl", "w") as f:
    for s in test_samples:
        f.write(json.dumps(s) + "\n")

print(f"Train samples saved: {len(train_samples)} → data/evaluation/csn_train.jsonl")
print(f"Test samples saved:  {len(test_samples)}  → data/evaluation/csn_test.jsonl")