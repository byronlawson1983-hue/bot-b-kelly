with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    lines = f.readlines()

# Find wallet line and add rpc_client after it
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if 'wallet = Keypair.from_base58_string(PRIVATE_KEY)' in line:
        # Add rpc_client right after wallet
        new_lines.append('from solana.rpc.api import Client as SyncClient\n')
        new_lines.append('rpc_client = SyncClient(RPC_ENDPOINT)\n')

# Also fix instant_test_analysis
content = ''.join(new_lines)
content = content.replace(
    'def instant_test_analysis(pnl):',
    'def instant_test_analysis(*args, **kwargs):'
)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added rpc_client and fixed instant_test_analysis")
