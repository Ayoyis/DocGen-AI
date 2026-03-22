"""
Manage test datasets for evaluation
"""
import json
import random
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TestDataManager:
    """Create and manage evaluation datasets"""
    
    def __init__(self, data_dir: str = "data/evaluation"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def create_from_codesearchnet(self, 
                                  codesearchnet_path: str,
                                  output_name: str = "test_set.jsonl",
                                  samples_per_lang: int = 100,
                                  languages: List[str] = None) -> str:
        """
        Create balanced test set from CodeSearchNet
        
        Args:
            codesearchnet_path: Path to CodeSearchNet data
            output_name: Name of output file
            samples_per_lang: Samples to extract per language
            languages: Which languages to include
        """
        if languages is None:
            languages = ['python', 'javascript', 'java', 'typescript', 'cpp']
        
        output_path = self.data_dir / output_name
        all_samples = []
        
        for lang in languages:
            lang_file = Path(codesearchnet_path) / f"{lang}" / "test.jsonl"
            if not lang_file.exists():
                logger.warning(f"Language file not found: {lang_file}")
                continue
            
            # Load and sample
            with open(lang_file, 'r') as f:
                lang_data = [json.loads(line) for line in f if line.strip()]
            
            # Filter for quality (code length, doc length)
            filtered = self._filter_quality(lang_data)
            
            # Sample randomly
            sampled = random.sample(filtered, min(samples_per_lang, len(filtered)))
            
            for item in sampled:
                all_samples.append({
                    'code': item['code'],
                    'doc': item['docstring'] if 'docstring' in item else item.get('documentation', ''),
                    'language': lang,
                    'code_type': self._detect_code_type(item['code']),
                    'source': 'codesearchnet',
                    'repo': item.get('repo', 'unknown'),
                    'path': item.get('path', 'unknown')
                })
        
        # Save
        with open(output_path, 'w') as f:
            for sample in all_samples:
                f.write(json.dumps(sample) + '\n')
        
        logger.info(f"Created test set with {len(all_samples)} samples at {output_path}")
        return str(output_path)
    
    def create_manual_test_set(self, samples: List[Dict], 
                               output_name: str = "manual_test.jsonl") -> str:
        """Create test set from manually curated examples"""
        output_path = self.data_dir / output_name
        
        with open(output_path, 'w') as f:
            for sample in samples:
                f.write(json.dumps(sample) + '\n')
        
        return str(output_path)
    
    def _filter_quality(self, data: List[Dict]) -> List[Dict]:
        """Filter for quality code-comment pairs"""
        filtered = []
        for item in data:
            code = item.get('code', '')
            doc = item.get('docstring', item.get('documentation', ''))
            
            # Filters
            code_lines = code.strip().split('\n')
            if len(code_lines) < 3 or len(code_lines) > 50:
                continue
            if len(doc.split()) < 3 or len(doc.split()) > 100:
                continue
            if 'TODO' in doc or 'FIXME' in doc:
                continue
            
            filtered.append(item)
        
        return filtered
    
    def _detect_code_type(self, code: str) -> str:
        """Detect if code is function, class, or module"""
        code = code.strip()
        
        # Check for class definition
        if any(line.strip().startswith('class ') for line in code.split('\n')):
            # Check if it's just a class or has other code
            lines = code.split('\n')
            class_lines = [l for l in lines if l.strip().startswith('class ')]
            if len(class_lines) == 1 and len(lines) < 20:
                return 'class'
        
        # Check for function/method
        if any(line.strip().startswith(('def ', 'function ', 'async def')) 
               for line in code.split('\n')):
            lines = code.split('\n')
            func_lines = [l for l in lines if l.strip().startswith(('def ', 'function '))]
            if len(func_lines) == 1 and len(lines) < 30:
                return 'function'
        
        return 'module'
    
    def load(self, filename: str = "test_set.jsonl") -> List[Dict]:
        """Load test set"""
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Test set not found: {filepath}")
        
        with open(filepath, 'r') as f:
            return [json.loads(line) for line in f if line.strip()]
    
    def get_stats(self, filename: str = "test_set.jsonl") -> Dict:
        """Get statistics about test set"""
        data = self.load(filename)
        
        stats = {
            'total': len(data),
            'by_language': {},
            'by_code_type': {},
            'avg_code_length': sum(len(d['code']) for d in data) / len(data),
            'avg_doc_length': sum(len(d['doc']) for d in data) / len(data)
        }
        
        for item in data:
            lang = item['language']
            ctype = item['code_type']
            stats['by_language'][lang] = stats['by_language'].get(lang, 0) + 1
            stats['by_code_type'][ctype] = stats['by_code_type'].get(ctype, 0) + 1
        
        return stats


# Example manual test samples for quick testing
QUICK_TEST_SAMPLES = [
    {
        'code': '''def calculate_total(price, quantity, tax_rate=0.1):
    subtotal = price * quantity
    tax = subtotal * tax_rate
    return subtotal + tax''',
        'doc': 'Calculates the total price including tax for a given price, quantity, and tax rate.',
        'language': 'python',
        'code_type': 'function'
    },
    {
        'code': '''class DataProcessor:
    def __init__(self, data):
        self.data = data
    
    def filter_by_value(self, min_value):
        return [x for x in self.data if x >= min_value]''',
        'doc': 'A class for processing data with methods to filter values.',
        'language': 'python',
        'code_type': 'class'
    },
    {
        'code': '''function fetchUserData(userId) {
    return fetch(`/api/users/${userId}`)
        .then(response => response.json())
        .then(data => {
            console.log('User loaded:', data);
            return data;
        })
        .catch(error => {
            console.error('Error fetching user:', error);
            throw error;
        });
}''',
        'doc': 'Fetches user data from the API by user ID and handles errors.',
        'language': 'javascript',
        'code_type': 'function'
    }
]