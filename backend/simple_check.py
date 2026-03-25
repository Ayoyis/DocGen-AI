# save as simple_check.py
import json

# Load your FAISS metadata
print("Loading metadata...")
with open('data/faiss/meta.jsonl', 'r', encoding='utf-8') as f:
    examples = [json.loads(line) for line in f.readlines()]

print(f"Total indexed examples: {len(examples)}")

# Show distribution by library/project
print("\nSample of indexed code:")
for i, ex in enumerate(examples[:5]):
    code = ex.get('code', '')
    doc = ex.get('doc', '')
    # Try to guess library from imports or function names
    first_line = code.split('\n')[0]
    print(f"\n{i+1}. {first_line[:80]}...")
    print(f"   Doc: {doc[:60]}...")