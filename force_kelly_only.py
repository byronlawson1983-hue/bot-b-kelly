with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# In buy() function, force trade_type to always be KELLY
# Find where trade_type is determined and override it
old = '''async def buy(mint,name,bonding,mc,creator,kelly=False):
    """Direct RPC buy via PumpPortal"""
    logger.info(f"🔧 BUY CALLED: {name[:20]} | mint: {mint[:8]}")
    global current_position,trades_in_cycle,should_restart,current_cycle_token'''

new = '''async def buy(mint,name,bonding,mc,creator,kelly=False):
    """Direct RPC buy via PumpPortal"""
    logger.info(f"🔧 BUY CALLED: {name[:20]} | mint: {mint[:8]}")
    kelly = True  # BOT B ALWAYS BUYS KELLY ONLY
    global current_position,trades_in_cycle,should_restart,current_cycle_token'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Bot B forced to Kelly-only mode")
