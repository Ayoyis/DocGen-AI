"""
Evaluation module for DocGen AI
Integrates with existing generator (CodeT5)
"""
import json
import numpy as np
import re
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

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
    Evaluator for DocGen AI system.
    Uses CodeT5 as generator and evaluates with BLEU, ROUGE-L, METEOR,
    and BERTScore (backed by CodeBERT for domain-aware semantic scoring).
    """

    def __init__(self, generator):
        self.generator = generator
        from .metrics import MetricsCalculator
        self.metrics_calc = MetricsCalculator()

        # Lazy-load BERTScore to avoid slow import at startup
        self._bert_score_fn = None

    def _get_bert_score_fn(self):
        """Lazy-load BERTScore function."""
        if self._bert_score_fn is None:
            from bert_score import score as bert_score
            self._bert_score_fn = bert_score
        return self._bert_score_fn

    def load_test_set(self, filepath: str) -> List[Dict]:
        """Load test dataset from JSONL file."""
        test_path = Path(filepath)
        if not test_path.exists():
            logger.error(f"Test set not found: {filepath}")
            return []
        with open(test_path, 'r', encoding='utf-8') as f:
            return [json.loads(line) for line in f if line.strip()]

    def build_prompt(self, code: str, language: str = "python") -> str:
        """
        Build zero-shot prompt for CodeT5.
        Truncated to 512 tokens worth of chars — CodeT5's input limit.
        """
        return f"Generate a concise docstring for this {language} code: {code[:512]}"

    def _normalize_text(self, text: str) -> str:
        """
        Normalize generated and reference text before metric calculation.
        Removes docstring markers, comment symbols, and extra whitespace
        so scores are not unfairly penalized for formatting differences.
        """
        text = text.strip()
        # Remove docstring quotes
        text = re.sub(r'^\"\"\"|\"\"\"$', '', text)
        text = re.sub(r"^'''|'''$", '', text)
        # Remove comment markers
        text = re.sub(r'^#\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^//\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^/\*\*?\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\*/?', '', text, flags=re.MULTILINE)
        # Remove JSDoc/Javadoc tags
        text = re.sub(r'@\w+\s*', '', text)
        # Lowercase and collapse whitespace
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text

    def generate_with_timing(self, code: str, language: str = "python") -> Tuple[str, float]:
        """Generate a comment for the given code and measure time taken."""
        start_time = time.perf_counter()
        prompt = self.build_prompt(code, language)
        generated = self.generator.generate_text(prompt, max_new_tokens=256)
        cleaned = self._clean_model_output(generated, prompt)

        # Fallback if cleaning wiped the output
        if not cleaned or len(cleaned.strip()) < 3:
            logger.warning("Empty output after cleaning — using raw output fallback")
            cleaned = generated.replace(prompt, "").strip()[:300] or "No documentation generated."

        elapsed = time.perf_counter() - start_time
        return cleaned, elapsed

    def _clean_model_output(self, text: str, prompt: str) -> str:
        """Clean model output by removing prompt echoes and formatting."""
        text = text.strip()

        # Remove prompt echo if present
        if prompt in text:
            text = text.replace(prompt, "").strip()

        # Remove lines that look like code
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith((
                'def ', 'class ', 'import ', 'from ',
                'return ', 'if ', 'for ', 'while '
            )):
                continue
            if not stripped:
                continue
            cleaned_lines.append(line)

        text = ' '.join(cleaned_lines).strip()

        # Remove common unwanted prefixes
        prefixes_to_remove = [
            'summarize:', 'summarize', 'documentation:', '/*', '*/',
            'code:', 'this code', 'the following', 'def ', 'class '
        ]
        lower_text = text.lower()
        for prefix in prefixes_to_remove:
            if lower_text.startswith(prefix):
                text = text[len(prefix):].strip()
                lower_text = text.lower()

        # Capitalize first letter
        if text and text[0].islower():
            text = text[0].upper() + text[1:]

        # Truncate if too long
        if len(text) > 300:
            text = text[:297] + "..."

        return text

    def _compute_bertscore(
        self,
        predictions: List[str],
        references: List[str]
    ) -> List[float]:
        """
        Compute BERTScore F1 using CodeBERT as the backbone.
        CodeBERT is used because it is domain-trained on code and
        natural language pairs, making it more appropriate for
        evaluating code comment generation than generic BERT.

        Layer 9 is recommended for CodeBERT-base as it captures
        the best semantic representations for this task.
        """
        bert_score = self._get_bert_score_fn()
        _, _, F1 = bert_score(
            predictions,
            references,
            model_type="microsoft/codebert-base",
            num_layers=9,
            batch_size=8,   # safe for CPU — increase if you have more RAM
            verbose=False
        )
        return F1.tolist()

    def evaluate_sample(self, sample: Dict) -> EvalResult:
        """Evaluate a single sample."""
        code = sample['code']
        language = sample['language']
        reference = sample['doc']
        code_type = sample.get('code_type', 'module')

        generated, gen_time = self.generate_with_timing(code, language)

        reference_norm = self._normalize_text(reference)
        generated_norm = self._normalize_text(generated)

        # Surface-level metrics
        metrics = self.metrics_calc.calculate_all(reference_norm, generated_norm)

        # BERTScore — computed per-batch in evaluate_batch for efficiency
        # Placeholder here; filled in by evaluate_batch
        metrics['bertscore_f1'] = 0.0

        return EvalResult(
            code=code,
            language=language,
            code_type=code_type,
            reference=reference,
            generated=generated,
            metrics=metrics,
            generation_time=gen_time
        )

    def evaluate_batch(
        self,
        test_set: List[Dict],
        save_path: Optional[str] = None
    ) -> Dict:
        """
        Evaluate the entire test set.
        BERTScore is computed in one batched call at the end for efficiency.
        """
        logger.info(f"Starting evaluation of {len(test_set)} samples")

        results = []
        errors = []

        for i, sample in enumerate(test_set):
            try:
                result = self.evaluate_sample(sample)
                results.append(result)
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(test_set)} samples")
            except Exception as e:
                logger.error(f"Error on sample {i}: {e}")
                errors.append({'index': i, 'error': str(e), 'sample': sample})

        # Batch BERTScore computation — much faster than per-sample calls
        if results:
            logger.info("Computing BERTScore in batch...")
            predictions = [
                self._normalize_text(r.generated) for r in results
            ]
            references = [
                self._normalize_text(r.reference) for r in results
            ]
            bertscore_f1s = self._compute_bertscore(predictions, references)
            for result, f1 in zip(results, bertscore_f1s):
                result.metrics['bertscore_f1'] = round(f1, 4)

        report = self._aggregate_results(results, errors)

        if save_path:
            self._save_results(results, report, save_path, errors)

        return report

    def _aggregate_results(
        self,
        results: List[EvalResult],
        errors: List[Dict]
    ) -> Dict:
        """Calculate aggregate statistics."""
        if not results:
            return {'error': 'No successful evaluations'}

        bleu_scores        = [r.metrics['bleu']          for r in results]
        rouge_scores       = [r.metrics['rougeL']        for r in results]
        meteor_scores      = [r.metrics['meteor']        for r in results]
        bertscore_f1_scores = [r.metrics['bertscore_f1'] for r in results]
        times              = [r.generation_time          for r in results]

        def calc_stats(values):
            return {
                'mean':   round(float(np.mean(values)),   4),
                'std':    round(float(np.std(values)),    4),
                'min':    round(float(np.min(values)),    4),
                'max':    round(float(np.max(values)),    4),
                'median': round(float(np.median(values)), 4),
            }

        report = {
            'summary': {
                'total_samples': len(results) + len(errors),
                'successful':    len(results),
                'failed':        len(errors),
                'success_rate':  round(
                    len(results) / max(len(results) + len(errors), 1), 3
                ),
            },
            'metrics': {
                'bleu':         calc_stats(bleu_scores),
                'rougeL':       calc_stats(rouge_scores),
                'meteor':       calc_stats(meteor_scores),
                'bertscore_f1': calc_stats(bertscore_f1_scores),
            },
            'performance': {
                'avg_generation_time_ms': round(
                    float(np.mean(times)) * 1000, 2
                ),
                'p95_generation_time_ms': round(
                    float(np.percentile(times, 95)) * 1000, 2
                ),
            }
        }

        # Breakdown by language
        by_language = {}
        for lang in set(r.language for r in results):
            lr = [r for r in results if r.language == lang]
            by_language[lang] = {
                'count':         len(lr),
                'bleu':          round(float(np.mean([r.metrics['bleu']          for r in lr])), 4),
                'rougeL':        round(float(np.mean([r.metrics['rougeL']        for r in lr])), 4),
                'meteor':        round(float(np.mean([r.metrics['meteor']        for r in lr])), 4),
                'bertscore_f1':  round(float(np.mean([r.metrics['bertscore_f1'] for r in lr])), 4),
            }
        report['by_language'] = by_language

        # Breakdown by code type
        by_type = {}
        for ctype in set(r.code_type for r in results):
            tr = [r for r in results if r.code_type == ctype]
            by_type[ctype] = {
                'count':         len(tr),
                'bleu':          round(float(np.mean([r.metrics['bleu']          for r in tr])), 4),
                'rougeL':        round(float(np.mean([r.metrics['rougeL']        for r in tr])), 4),
                'meteor':        round(float(np.mean([r.metrics['meteor']        for r in tr])), 4),
                'bertscore_f1':  round(float(np.mean([r.metrics['bertscore_f1'] for r in tr])), 4),
            }
        report['by_code_type'] = by_type

        return report

    def _save_results(
        self,
        results: List[EvalResult],
        report: Dict,
        save_path: str,
        errors: List[Dict]
    ):
        """Save evaluation results to files."""
        save_dir = Path(save_path)
        save_dir.mkdir(parents=True, exist_ok=True)

        with open(save_dir / 'detailed_results.json', 'w') as f:
            json.dump([r.to_dict() for r in results], f, indent=2)
        with open(save_dir / 'report.json', 'w') as f:
            json.dump(report, f, indent=2)
        if errors:
            with open(save_dir / 'errors.json', 'w') as f:
                json.dump(errors, f, indent=2)

        self._save_text_report(report, save_dir / 'summary.txt')
        logger.info(f"Results saved to {save_dir}")

    def _save_text_report(self, report: Dict, path: Path):
        """Generate human-readable summary report."""
        with open(path, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("DocGen AI Evaluation Report\n")
            f.write("=" * 60 + "\n\n")

            s = report['summary']
            f.write(f"Total Samples:  {s['total_samples']}\n")
            f.write(f"Successful:     {s['successful']}\n")
            f.write(f"Failed:         {s['failed']}\n")
            f.write(f"Success Rate:   {s['success_rate'] * 100:.1f}%\n\n")

            f.write("-" * 40 + "\n")
            f.write("Automated Metrics\n")
            f.write("-" * 40 + "\n")
            for metric, stats in report['metrics'].items():
                f.write(f"{metric.upper()}:\n")
                f.write(f"  Mean:   {stats['mean']:.4f} (±{stats['std']:.4f})\n")
                f.write(f"  Range:  [{stats['min']:.4f}, {stats['max']:.4f}]\n\n")

            f.write("-" * 40 + "\n")
            f.write("Performance\n")
            f.write("-" * 40 + "\n")
            p = report['performance']
            f.write(f"Avg Generation Time: {p['avg_generation_time_ms']:.1f}ms\n")
            f.write(f"P95 Generation Time: {p['p95_generation_time_ms']:.1f}ms\n\n")

            f.write("-" * 40 + "\n")
            f.write("Results by Language\n")
            f.write("-" * 40 + "\n")
            for lang, stats in report.get('by_language', {}).items():
                f.write(
                    f"{lang}: n={stats['count']}, "
                    f"BLEU={stats['bleu']:.4f}, "
                    f"ROUGE-L={stats['rougeL']:.4f}, "
                    f"METEOR={stats['meteor']:.4f}, "
                    f"BERTScore-F1={stats['bertscore_f1']:.4f}\n"
                )

            f.write("\n" + "-" * 40 + "\n")
            f.write("Results by Code Type\n")
            f.write("-" * 40 + "\n")
            for ctype, stats in report.get('by_code_type', {}).items():
                f.write(
                    f"{ctype}: n={stats['count']}, "
                    f"BLEU={stats['bleu']:.4f}, "
                    f"ROUGE-L={stats['rougeL']:.4f}, "
                    f"METEOR={stats['meteor']:.4f}, "
                    f"BERTScore-F1={stats['bertscore_f1']:.4f}\n"
                )

            f.write("\n" + "=" * 60 + "\n")