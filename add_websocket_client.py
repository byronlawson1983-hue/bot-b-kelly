with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add websocket imports at the top
if 'import websockets' not in content:
    old_imports = "import asyncio"
    new_imports = """import asyncio
import websockets
import json"""
    content = content.replace(old_imports, new_imports, 1)

# Add websocket initialization after wallet
if 'ws = None' not in content:
    old_wallet = "rpc_client = SyncClient(RPC_ENDPOINT)"
    new_wallet = """rpc_client = SyncClient(RPC_ENDPOINT)

# Websocket for price feeds
ws = None
latest_data = {}  # Store latest price data per mint"""
    content = content.replace(old_wallet, new_wallet)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added websocket client initialization")
