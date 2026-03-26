# verify_results.py
import json
from app.evaluation import DocGenEvaluator
from app.generator import CodeT5Generator

def verify_results():
    # Load your test set
    with open('data/evaluation/csn_test.jsonl', 'r', encoding='utf-8') as f:
        samples = [json.loads(line) for line in f.readlines()]
    
    # Initialize your generator (same as your app)
    generator = CodeT5Generator()
    
    print("=" * 70)
    print("VERIFICATION: Checking if results are real or bug")
    print("=" * 70)
    
    # Check 5 samples
    for i, sample in enumerate(samples[:5]):
        code = sample['code']
        reference = sample['doc']
        
        # Generate (no RAG)
        prompt = f"summarize: {code[:400]}"
        generated = generator.generate_text(prompt, max_new_tokens=128)
        
        # Clean output
        generated = generated.strip()
        reference = reference.strip()
        
        print(f"\n{'='*70}")
        print(f"SAMPLE {i+1}")
        print(f"{'='*70}")
        
        print(f"\nCODE (first 150 chars):\n{code[:150]}...")
        
        print(f"\nGENERATED (full):\n{generated}")
        
        print(f"\nREFERENCE (full):\n{reference}")
        
        print(f"\nCOMPARISON:")
        print(f"  Exact match: {generated == reference}")
        print(f"  Generated length: {len(generated)}")
        print(f"  Reference length: {len(reference)}")
        
        # Calculate metrics manually
        from app.metrics import MetricsCalculator
        m = MetricsCalculator()
        scores = m.calculate_all(reference, generated)
        print(f"\nMETRICS:")
        for k, v in scores.items():
            print(f"  {k}: {v:.4f}")

if __name__ == "__main__":
    verify_results()