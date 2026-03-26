import requests
import json
from datetime import datetime

response = requests.post(
    "http://localhost:8000/evaluate/compare",
    json={"test_set": "train.jsonl", "max_samples": 80}
)

if response.status_code == 200:
    results = response.json()
    
    # Save to file
    filename = f"evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    #rag = results['with_rag']
    no_rag = results['without_rag']
    #imp = results['improvement']
    
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    #print(f"With RAG:")
    #print(f"  BLEU:    {rag['bleu']:.4f}")
    #print(f"  ROUGE-L: {rag['rougeL']:.4f}")
    #print(f"  METEOR:  {rag['meteor']:.4f}")
    #print(f"  Time:    {rag['avg_time_ms']:.1f}ms")

    print(f"\nWithout RAG:")
    print(f"  BLEU:    {no_rag['bleu']:.4f}")
    print(f"  ROUGE-L: {no_rag['rougeL']:.4f}")
    print(f"  METEOR:  {no_rag['meteor']:.4f}")
    print(f"  BERTScore: {no_rag['bertscore']:.4f}")
    print(f"  Time:    {no_rag['avg_time_ms']:.1f}ms")
    
    #print(f"\nImprovement:")
    #print(f"  BLEU:    {imp['bleu']:+.4f}")
    #print(f"  ROUGE-L: {imp['rougeL']:+.4f}")
    #print(f"  METEOR:  {imp['meteor']:+.4f}")
    
    print(f"\nSaved to: {filename}")
    print("="*60)