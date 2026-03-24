with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# In buy(), force KELLY trade type when called from signal
# Find where trade_type is determined and force it to KELLY
old = '''    kelly = True  # BOT B ALWAYS BUYS KELLY ONLY
    global current_position,trades_in_cycle,should_restart,current_cycle_token'''

new = '''    kelly = True  # BOT B ALWAYS BUYS KELLY ONLY
    global current_position,trades_in_cycle,should_restart,current_cycle_token
    
    # BOT B ALWAYS USES KELLY TRADE TYPE
    trade_type = "KELLY"
    base_amount = KELLY_AMOUNT'''

# Remove all the trade_type logic since we're forcing KELLY
content = content.replace(old, new)

# Also skip the trade_type determination section
old_logic = '''    if trade_type not in ["REAL", "KELLY"]:
        logger.info(f"❌ Bot B only handles KELLY, skipping {trade_type}")
        return False'''

new_logic = '''    # Bot B always uses KELLY - skip validation
    logger.info(f"💰 KELLY BUY: {name} @ {bonding}% | {base_amount:.6f} SOL")'''

content = content.replace(old_logic, new_logic)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Forced KELLY trade_type for all Bot B buys")
