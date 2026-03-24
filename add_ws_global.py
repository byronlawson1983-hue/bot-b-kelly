with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add ws_global with the websocket globals
old = """# Websocket for price feeds
ws = None
latest_data = {}  # Store latest price data per mint"""

new = """# Websocket for price feeds
ws = None
ws_global = None  # Global websocket connection
latest_data = {}  # Store latest price data per mint"""

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added ws_global")
