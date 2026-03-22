import json
from pathlib import Path

# Create data/evaluation directory
Path("data/evaluation").mkdir(parents=True, exist_ok=True)

# Quick test samples (same as in your test_data.py)
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

# Save to file
with open("data/evaluation/quick_test.jsonl", "w") as f:
    for sample in QUICK_TEST_SAMPLES:
        f.write(json.dumps(sample) + "\n")

print("Created quick_test.jsonl with 3 samples")