with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add send_with_retry function before buy()
send_retry_func = '''
async def send_with_retry(tx, max_retries=3):
    """Send transaction with retries"""
    for attempt in range(max_retries):
        try:
            from solana.rpc.types import TxOpts
            from solana.rpc.commitment import Confirmed
            sig = await client.send_transaction(tx, opts=TxOpts(skip_confirmation=False, preflight_commitment=Confirmed))
            return str(sig.value)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(1)
    return None

'''

# Insert before buy()
content = content.replace('async def buy(', send_retry_func + 'async def buy(')

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added send_with_retry")
