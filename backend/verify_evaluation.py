# verify_evaluation.py (fixed)
import json
import time
from app.generator import CodeT5Generator

# Load a few test samples
with open('data/evaluation/csn_test.jsonl', 'r') as f:
    samples = [json.loads(line) for line in f.readlines()[:3]]

# Initialize with NEURAL model
generator = CodeT5Generator()  # This loads codet5-base-multi-sum

print("=" * 60)
print("VERIFYING EVALUATION WITH NEURAL MODEL")
print("=" * 60)

for i, sample in enumerate(samples):
    code = sample['code']
    reference = sample['doc']
    
    # Generate with neural model (direct, not through evaluator)
    start = time.perf_counter()
    generated = generator.generate_docstring(code, 'python')
    elapsed = (time.perf_counter() - start) * 1000
    
    print(f"\nSample {i+1}:")
    print(f"Code: {code[:60]}...")
    print(f"Generated: {generated}")
    print(f"Reference: {reference}")
    print(f"Time: {elapsed:.2f}ms")
    
    # Check if it's actually neural (should be specific, not generic)
    is_pattern = generated.startswith('"""Handle') or generated.startswith('"""Returns') or 'Handles ' in generated
    is_neural = not is_pattern
    print(f"Is neural (not pattern): {is_neural}")
    
    # Check similarity
    from app.metrics import MetricsCalculator
    m = MetricsCalculator()
    scores = m.calculate_all(reference, generated)
    print(f"BLEU: {scores['bleu']:.4f}")