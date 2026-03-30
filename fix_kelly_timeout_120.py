with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Fix the kelly_timeout line to be 120 seconds
old = 'kelly_timeout = random.randint(10, 15) if trade_type == "KELLY" else random.randint(TIMEOUT_MIN, TIMEOUT_MAX)'
new = 'kelly_timeout = 120  # Match Bot A KELLY timeout'

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Kelly timeout fixed to 120 seconds")
