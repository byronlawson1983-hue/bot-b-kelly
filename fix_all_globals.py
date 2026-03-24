with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Find where globals are defined and add ALL missing ones
old = """# Bot B specific settings
KELLY_AMOUNT = 0.005
bought_mints = set()
current_position = None
blacklist = set()"""

new = """# Bot B specific settings
KELLY_AMOUNT = 0.005
bought_mints = set()
current_position = None
blacklist = set()
token_blacklist = set()
should_restart = False
test_approved_tokens = set()
kelly_approved_tokens = set()
test2_approved_tokens = set()
real_approved_tokens = set()
recycled_tokens = set()
recycling_queued = False"""

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ All globals added")
