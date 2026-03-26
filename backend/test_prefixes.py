from app.generator import CodeT5Generator

g = CodeT5Generator(model_name='Salesforce/codet5-base-multi-sum')

test_cases = [
    "def get_vid_from_url(url):\n    return match1(url, r'youtu\\.be/([^?/]+)')",
    "def svg_to_image(string, size=None):\n    if isinstance(string, unicode):\n        string = string.encode('utf-8')",
]

for code in test_cases:
    result = g.generate_text(code, max_new_tokens=20)
    print(f"Code: {code[:40]}...")
    print(f"Result: {result}")
    print("-" * 50)