with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add get_balance function before check_dev_wallet
get_balance_func = '''
def get_balance():
    """Get wallet SOL balance"""
    try:
        from solana.rpc.api import Client
        client = Client(RPC_ENDPOINT)
        balance = client.get_balance(wallet.pubkey()).value / 1e9
        return balance
    except:
        return 0

'''

# Insert before check_dev_wallet
content = content.replace('def check_dev_wallet', get_balance_func + 'def check_dev_wallet')

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added get_balance function")
