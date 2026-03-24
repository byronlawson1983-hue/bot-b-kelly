with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add stats dict with other globals
old = "recycling_queued = False"
new = """recycling_queued = False
stats = {"test_trades": 0, "kelly_trades": 0, "real_trades": 0}"""

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added stats dict")
