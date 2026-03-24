with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Find the buy function and add logging at the start
old = '''async def buy(mint,name,bonding,mc,creator,kelly=False):
    """Direct RPC buy via PumpPortal"""'''

new = '''async def buy(mint,name,bonding,mc,creator,kelly=False):
    """Direct RPC buy via PumpPortal"""
    logger.info(f"🔧 BUY CALLED: {name[:20]} | mint: {mint[:8]}")'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added buy() entry logging")
