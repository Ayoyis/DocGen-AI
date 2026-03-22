"""
Metric calculations for code comment evaluation
"""
import re
import math
from typing import Dict, List
from collections import Counter


class MetricsCalculator:
    """Calculate NLG metrics for generated comments - all custom implementations"""
    
    def tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        if not text:
            return []
        return re.findall(r'\b\w+\b', text.lower())
    
    def calculate_all(self, reference: str, hypothesis: str) -> Dict[str, float]:
        """Calculate all metrics"""
        # Handle empty strings
        if not reference or not hypothesis:
            return {
                'bleu': 0.0,
                'rouge1': 0.0,
                'rouge2': 0.0,
                'rougeL': 0.0,
                'meteor': 0.0,
            }
        
        return {
            'bleu': self.bleu(reference, hypothesis),
            'rouge1': self.rouge_n(reference, hypothesis, 1),
            'rouge2': self.rouge_n(reference, hypothesis, 2),
            'rougeL': self.rouge_l(reference, hypothesis),
            'meteor': self.meteor(reference, hypothesis),
        }
    
    def bleu(self, reference: str, hypothesis: str, max_n: int = 4) -> float:
        """Calculate BLEU score (custom implementation)"""
        ref_tokens = self.tokenize(reference)
        hyp_tokens = self.tokenize(hypothesis)
        
        if not ref_tokens or not hyp_tokens:
            return 0.0
        
        # Calculate precision for n-grams
        precisions = []
        for n in range(1, max_n + 1):
            ref_ngrams = self._get_ngrams(ref_tokens, n)
            hyp_ngrams = self._get_ngrams(hyp_tokens, n)
            
            if not hyp_ngrams:
                precisions.append(0.0)
                continue
            
            matches = sum((hyp_ngrams & ref_ngrams).values())
            total = sum(hyp_ngrams.values())
            
            if total == 0:
                precisions.append(0.0)
            else:
                precisions.append(matches / total)
        
        # Geometric mean with smoothing
        if all(p > 0 for p in precisions):
            geo_mean = math.exp(sum(math.log(p) for p in precisions) / len(precisions))
        else:
            # Use smoothing - replace zeros with small value
            smoothed = [p if p > 0 else 0.01 for p in precisions]
            geo_mean = math.exp(sum(math.log(p) for p in smoothed) / len(smoothed))
        
        # Brevity penalty
        bp = min(1.0, math.exp(1 - len(ref_tokens) / max(len(hyp_tokens), 1)))
        
        return round(bp * geo_mean, 4)
    
    def _get_ngrams(self, tokens: List[str], n: int) -> Counter:
        """Extract n-grams from tokens"""
        if len(tokens) < n:
            return Counter()
        ngrams = zip(*[tokens[i:] for i in range(n)])
        return Counter(ngrams)
    
    def rouge_n(self, reference: str, hypothesis: str, n: int) -> float:
        """Calculate ROUGE-N score"""
        ref_tokens = self.tokenize(reference)
        hyp_tokens = self.tokenize(hypothesis)
        
        if not ref_tokens or not hyp_tokens:
            return 0.0
        
        ref_ngrams = self._get_ngrams(ref_tokens, n)
        hyp_ngrams = self._get_ngrams(hyp_tokens, n)
        
        if not ref_ngrams or not hyp_ngrams:
            return 0.0
        
        matches = sum((hyp_ngrams & ref_ngrams).values())
        recall = matches / max(sum(ref_ngrams.values()), 1)
        precision = matches / max(sum(hyp_ngrams.values()), 1)
        
        if precision + recall == 0:
            return 0.0
        return round(2 * precision * recall / (precision + recall), 4)
    
    def rouge_l(self, reference: str, hypothesis: str) -> float:
        """Calculate ROUGE-L (LCS-based)"""
        ref_tokens = self.tokenize(reference)
        hyp_tokens = self.tokenize(hypothesis)
        
        if not ref_tokens or not hyp_tokens:
            return 0.0
        
        lcs_length = self._lcs_length(ref_tokens, hyp_tokens)
        
        if lcs_length == 0:
            return 0.0
        
        recall = lcs_length / len(ref_tokens)
        precision = lcs_length / len(hyp_tokens)
        
        if precision + recall == 0:
            return 0.0
        return round(2 * precision * recall / (precision + recall), 4)
    
    def _lcs_length(self, seq1: List[str], seq2: List[str]) -> int:
        """Calculate length of longest common subsequence"""
        if not seq1 or not seq2:
            return 0
        
        m, n = len(seq1), len(seq2)
        # Use 1D DP for memory efficiency
        prev = [0] * (n + 1)
        curr = [0] * (n + 1)
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    curr[j] = prev[j-1] + 1
                else:
                    curr[j] = max(prev[j], curr[j-1])
            prev, curr = curr, prev  # Swap rows
        
        return prev[n]
    
    def meteor(self, reference: str, hypothesis: str) -> float:
        """Simplified METEOR approximation"""
        ref_tokens = set(self.tokenize(reference))
        hyp_tokens = set(self.tokenize(hypothesis))
        
        if not ref_tokens or not hyp_tokens:
            return 0.0
        
        matches = len(ref_tokens & hyp_tokens)
        precision = matches / len(hyp_tokens)
        recall = matches / len(ref_tokens)
        
        if precision + recall == 0:
            return 0.0
        return round(2 * precision * recall / (precision + recall), 4)