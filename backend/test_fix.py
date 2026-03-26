# test_fix.py
from app.generator import CodeT5Generator

g = CodeT5Generator()

# Use the format CodeT5 was actually trained on
test_code = "def get_vid_from_url(url):\n    return match1(url, r'youtu\\.be/([^?/]+)')"

# This is what CodeT5 expects
result = g.generate_text(f"generate documentation: {test_code}", max_new_tokens=50)
print(f"Generated: {result}")
print(f"Length: {len(result)}")

# Should now output: "Extracts video ID from URL" or similar