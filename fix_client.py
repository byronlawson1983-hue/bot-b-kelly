with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Remove the comment and restore client
old = "# client = AsyncClient(RPC_ENDPOINT)  # Not needed for get_balance"
new = "client = AsyncClient(RPC_ENDPOINT)"

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Restored client")
