with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Find and replace KELLY_AMOUNT
import re
content = re.sub(r'KELLY_AMOUNT\s*=\s*0\.01\d*', 'KELLY_AMOUNT = 0.013', content)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ KELLY_AMOUNT set to 0.013")
