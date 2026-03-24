with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Fix emit calls - remove or fix them
content = content.replace("emit()", "# emit() - disabled")

# Add latest_data as a global dict at the top with other globals
old = "stats = {\"test_trades\": 0, \"kelly_trades\": 0, \"real_trades\": 0, \"total_trades\": 0, \"recent_trades\": []}"
new = """stats = {"test_trades": 0, "kelly_trades": 0, "real_trades": 0, "total_trades": 0, "recent_trades": []}
latest_data = {}  # Track latest price data for monitoring"""

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Fixed emit() and added latest_data")
