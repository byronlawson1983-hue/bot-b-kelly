with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Make sure AsyncClient is imported
if "from solana.rpc.async_api import AsyncClient" not in content:
    # Add it after other imports
    content = content.replace(
        "from solana.rpc.async_api import AsyncClient",
        "from solana.rpc.async_api import AsyncClient",
        1
    )
    # If that didn't work, add it at the top
    if "AsyncClient" not in content.split('\n')[0:20]:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('import') or line.startswith('from'):
                continue
            else:
                lines.insert(i, 'from solana.rpc.async_api import AsyncClient')
                break
        content = '\n'.join(lines)

# Also change AsyncClient to regular Client for get_balance
content = content.replace(
    "client = AsyncClient(RPC_ENDPOINT)",
    "# client = AsyncClient(RPC_ENDPOINT)  # Not needed for get_balance"
)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Fixed AsyncClient")
