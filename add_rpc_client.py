with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add rpc_client initialization after wallet
old = """# Initialize wallet
import base58
wallet = Keypair.from_base58_string(PRIVATE_KEY)
# client = AsyncClient(RPC_ENDPOINT)  # Not needed for get_balance"""

new = """# Initialize wallet
import base58
from solana.rpc.api import Client as SyncClient
wallet = Keypair.from_base58_string(PRIVATE_KEY)
client = AsyncClient(RPC_ENDPOINT)
rpc_client = SyncClient(RPC_ENDPOINT)  # Sync client for sell()"""

content = content.replace(old, new)

# Also add instant_test_analysis stub
stub = '''
def instant_test_analysis(pnl):
    """Stub - not needed for Bot B"""
    return False

'''

content = content.replace('async def subscribe_to_token', stub + 'async def subscribe_to_token')

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added rpc_client and instant_test_analysis")
