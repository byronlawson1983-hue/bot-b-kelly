with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    lines = f.readlines()

# Find buy() function and replace trade_type determination
new_lines = []
in_buy = False
skip_until_amount = False

for i, line in enumerate(lines):
    if 'async def buy(mint,name,bonding,mc,creator,kelly=False):' in line:
        in_buy = True
        new_lines.append(line)
        continue
    
    # After buy() starts, inject KELLY forcing
    if in_buy and 'global current_position' in line:
        new_lines.append(line)
        new_lines.append('    \n')
        new_lines.append('    # BOT B: ALWAYS KELLY\n')
        new_lines.append('    trade_type = "KELLY"\n')
        new_lines.append('    base_amount = KELLY_AMOUNT\n')
        new_lines.append('    \n')
        skip_until_amount = True
        continue
    
    # Skip all trade_type determination logic
    if skip_until_amount:
        if 'logger.info(f"💰' in line:
            skip_until_amount = False
            # Replace with KELLY log
            new_lines.append('    logger.info(f"💰 KELLY BUY: {name} @ {bonding}% | {base_amount:.6f} SOL")\n')
            continue
        else:
            continue
    
    if in_buy and 'async def ' in line and 'buy(' not in line:
        in_buy = False
    
    new_lines.append(line)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.writelines(new_lines)

print("✅ Simplified Bot B to KELLY only")
