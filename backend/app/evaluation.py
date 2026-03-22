"""
Evaluation module for DocGen AI
Integrates with existing generator and retriever
"""
import json
import numpy as np
import re
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EvalResult:
    """Single evaluation result"""
    code: str
    language: str
    code_type: str
    reference: str
    generated: str
    metrics: Dict[str, float]
    generation_time: float
    
    def to_dict(self) -> Dict:
        return {
            'code': self.code[:200] + '...' if len(self.code) > 200 else self.code,
            'language': self.language,
            'code_type': self.code_type,
            'reference': self.reference,
            'generated': self.generated,
            'metrics': self.metrics,
            'generation_time_ms': round(self.generation_time * 1000, 2)
        }


class DocGenEvaluator:
    """
    Evaluator that integrates with your existing DocGen AI system
    """
    
    def __init__(self, generator, retriever=None):
        """
        Args:
            generator: Your existing CodeT5Generator instance
            retriever: Optional CodeBERTRetriever for RAG evaluation
        """
        self.generator = generator
        self.retriever = retriever
        
        # Import metrics here to avoid circular imports
        from .metrics import MetricsCalculator
        self.metrics_calc = MetricsCalculator()
    
    def load_test_set(self, filepath: str) -> List[Dict]:
        """Load test dataset"""
        test_path = Path(filepath)
        if not test_path.exists():
            logger.error(f"Test set not found: {filepath}")
            return []
        
        with open(test_path, 'r', encoding='utf-8') as f:
            return [json.loads(line) for line in f if line.strip()]
    
    def generate_with_timing(self, code: str, language: str, 
                           use_retrieval: bool = True) -> Tuple[str, float]:
        """Generate comment and measure time"""
        start_time = time.perf_counter()
        
        # Use standard module generation (works for all code types)
        # Note: use_retrieval flag is for comparison metrics only
        # since your generator doesn't have RAG-aware generation
        generated = self.generator.generate_module_docstring(code, language)
        
        elapsed = time.perf_counter() - start_time
        return generated, elapsed
    
    def evaluate_sample(self, sample: Dict, use_retrieval: bool = True) -> EvalResult:
        """Evaluate single sample"""
        code = sample['code']
        language = sample['language']
        reference = sample['doc']
        code_type = sample.get('code_type', 'module')
        
        # Generate
        generated, gen_time = self.generate_with_timing(code, language, use_retrieval)
        
        # Calculate metrics
        metrics = self.metrics_calc.calculate_all(reference, generated)
        
        return EvalResult(
            code=code,
            language=language,
            code_type=code_type,
            reference=reference,
            generated=generated,
            metrics=metrics,
            generation_time=gen_time
        )
    
    def evaluate_batch(self, test_set: List[Dict], 
                      use_retrieval: bool = True,
                      save_path: Optional[str] = None) -> Dict:
        """
        Evaluate entire test set
        
        Args:
            test_set: List of test samples
            use_retrieval: Whether to use RAG (for metrics comparison)
            save_path: Where to save detailed results
        """
        logger.info(f"Starting evaluation of {len(test_set)} samples")
        
        results = []
        errors = []
        
        for i, sample in enumerate(test_set):
            try:
                result = self.evaluate_sample(sample, use_retrieval)
                results.append(result)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i+1}/{len(test_set)} samples")
                    
            except Exception as e:
                logger.error(f"Error on sample {i}: {e}")
                errors.append({'index': i, 'error': str(e), 'sample': sample})
        
        # Aggregate statistics
        report = self._aggregate_results(results, errors)
        
        # Save detailed results
        if save_path:
            self._save_results(results, report, save_path, errors)
        
        return report
    
    def _aggregate_results(self, results: List[EvalResult], 
                          errors: List[Dict]) -> Dict:
        """Calculate aggregate statistics"""
        if not results:
            return {'error': 'No successful evaluations'}
        
        # Extract metric values
        bleu_scores = [r.metrics['bleu'] for r in results]
        rouge_scores = [r.metrics['rougeL'] for r in results]
        meteor_scores = [r.metrics['meteor'] for r in results]
        times = [r.generation_time for r in results]
        
        def calc_stats(values):
            if not values:
                return {}
            return {
                'mean': round(np.mean(values), 4),
                'std': round(np.std(values), 4),
                'min': round(np.min(values), 4),
                'max': round(np.max(values), 4),
                'median': round(np.median(values), 4)
            }
        
        report = {
            'summary': {
                'total_samples': len(results) + len(errors),
                'successful': len(results),
                'failed': len(errors),
                'success_rate': round(len(results) / (len(results) + len(errors)), 3)
            },
            'metrics': {
                'bleu': calc_stats(bleu_scores),
                'rougeL': calc_stats(rouge_scores),
                'meteor': calc_stats(meteor_scores),
            },
            'performance': {
                'avg_generation_time_ms': round(np.mean(times) * 1000, 2),
                'p95_generation_time_ms': round(np.percentile(times, 95) * 1000, 2),
            }
        }
        
        # Breakdown by language
        by_language = {}
        for lang in set(r.language for r in results):
            lang_results = [r for r in results if r.language == lang]
            by_language[lang] = {
                'count': len(lang_results),
                'bleu': round(np.mean([r.metrics['bleu'] for r in lang_results]), 4),
                'rougeL': round(np.mean([r.metrics['rougeL'] for r in lang_results]), 4)
            }
        report['by_language'] = by_language
        
        # Breakdown by code type
        by_type = {}
        for ctype in set(r.code_type for r in results):
            type_results = [r for r in results if r.code_type == ctype]
            by_type[ctype] = {
                'count': len(type_results),
                'bleu': round(np.mean([r.metrics['bleu'] for r in type_results]), 4),
                'rougeL': round(np.mean([r.metrics['rougeL'] for r in type_results]), 4)
            }
        report['by_code_type'] = by_type
        
        return report
    
    def _save_results(self, results: List[EvalResult], report: Dict, 
                     save_path: str, errors: List[Dict]):
        """Save evaluation results to files"""
        save_dir = Path(save_path)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Save detailed results
        detailed = [r.to_dict() for r in results]
        with open(save_dir / 'detailed_results.json', 'w') as f:
            json.dump(detailed, f, indent=2)
        
        # Save report
        with open(save_dir / 'report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save errors
        if errors:
            with open(save_dir / 'errors.json', 'w') as f:
                json.dump(errors, f, indent=2)
        
        # Save human-readable summary
        self._save_text_report(report, save_dir / 'summary.txt')
        
        logger.info(f"Results saved to {save_dir}")
    
    def _save_text_report(self, report: Dict, path: Path):
        """Generate human-readable report"""
        with open(path, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("DocGen AI Evaluation Report\n")
            f.write("=" * 60 + "\n\n")
            
            # Summary
            s = report['summary']
            f.write(f"Total Samples: {s['total_samples']}\n")
            f.write(f"Successful: {s['successful']}\n")
            f.write(f"Failed: {s['failed']}\n")
            f.write(f"Success Rate: {s['success_rate']*100:.1f}%\n\n")
            
            # Metrics
            f.write("-" * 40 + "\n")
            f.write("Automated Metrics\n")
            f.write("-" * 40 + "\n")
            for metric, stats in report['metrics'].items():
                f.write(f"{metric.upper()}:\n")
                f.write(f"  Mean: {stats['mean']:.4f} (±{stats['std']:.4f})\n")
                f.write(f"  Range: [{stats['min']:.4f}, {stats['max']:.4f}]\n\n")
            
            # Performance
            f.write("-" * 40 + "\n")
            f.write("Performance\n")
            f.write("-" * 40 + "\n")
            p = report['performance']
            f.write(f"Avg Generation Time: {p['avg_generation_time_ms']:.1f}ms\n")
            f.write(f"P95 Generation Time: {p['p95_generation_time_ms']:.1f}ms\n\n")
            
            # By Language
            f.write("-" * 40 + "\n")
            f.write("Results by Language\n")
            f.write("-" * 40 + "\n")
            for lang, stats in report['by_language'].items():
                f.write(f"{lang}: n={stats['count']}, "
                       f"BLEU={stats['bleu']:.4f}, ROUGE-L={stats['rougeL']:.4f}\n")
            
            f.write("\n" + "=" * 60 + "\n")