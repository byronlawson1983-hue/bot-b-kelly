with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add TIMEOUT_MIN and TIMEOUT_MAX constants
old = "VOLUME_DEATH_SECONDS = 10  # Dead token detection"
new = """VOLUME_DEATH_SECONDS = 10  # Dead token detection
TIMEOUT_MIN = 10
TIMEOUT_MAX = 15"""

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added TIMEOUT_MIN and TIMEOUT_MAX")
