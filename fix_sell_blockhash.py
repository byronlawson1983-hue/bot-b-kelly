with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Fix the sell to use client directly, not asyncio.to_thread
old_send = '''            result = await asyncio.to_thread(
                rpc_client.send_transaction, signed
            )'''

new_send = '''            # Send using sync client directly
            from solana.rpc.types import TxOpts
            from solana.rpc.commitment import Confirmed
            result = rpc_client.send_transaction(signed, opts=TxOpts(skip_preflight=False))'''

content = content.replace(old_send, new_send)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Fixed sell to use sync send_transaction")
