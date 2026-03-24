with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add should_restart at the top with other globals
old = "bought_mints = set()"
new = """bought_mints = set()
should_restart = False"""

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Fixed should_restart")
