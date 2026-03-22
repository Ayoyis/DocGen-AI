# create_test_set_from_download.py
import json
import random
from pathlib import Path

random.seed(42)

data_file = Path("data/processed/python_train.jsonl")
test_output = Path("data/evaluation/codesearchnet_test.jsonl")

test_output.parent.mkdir(parents=True, exist_ok=True)

print("Loading data...")
all_data = []
with open(data_file, 'r', encoding='utf-8') as f:  # <-- ADD encoding='utf-8'
    for line in f:
        all_data.append(json.loads(line))

print(f"Total samples: {len(all_data)}")

random.shuffle(all_data)
split_idx = int(len(all_data) * 0.8)
train_data = all_data[:split_idx]
test_data = all_data[split_idx:]

test_data = test_data[:100]

formatted_test = []
for item in test_data:
    code = item['code']
    code_type = 'module'
    if 'class ' in code:
        code_type = 'class'
    elif 'def ' in code:
        code_type = 'function'
    
    formatted_test.append({
        'code': code,
        'doc': item['doc'],
        'language': 'python',
        'code_type': code_type
    })

with open(test_output, 'w', encoding='utf-8') as f:  # <-- ADD encoding='utf-8'
    for item in formatted_test:
        f.write(json.dumps(item) + '\n')

with open(data_file, 'w', encoding='utf-8') as f:  # <-- ADD encoding='utf-8'
    for item in train_data:
        f.write(json.dumps(item) + '\n')

print(f"\nTest set: {len(formatted_test)} samples")
print(f"Training set: {len(train_data)} samples")