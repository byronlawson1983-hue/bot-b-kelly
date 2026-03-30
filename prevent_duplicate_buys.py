with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Find where Bot B decides to buy and add duplicate check
# Look for where it reads the signal and calls buy()

old = '''        if signals:
            for sig in signals:
                mint = sig.get("mint")
                name = sig.get("name")
                peak = sig.get("peak")
                logger.info(f"SIGNAL: {name} @ +{peak:.1f}%")
                logger.info(f"KELLY BUY: {mint[:8]}... | {KELLY_BET_SIZE} SOL")
                await buy(mint)'''

new = '''        if signals:
            for sig in signals:
                mint = sig.get("mint")
                name = sig.get("name")
                peak = sig.get("peak")
                
                # Check if we already have a position on this mint
                if current_position and current_position.get("mint") == mint:
                    logger.info(f"⚠️ SKIPPING: Already have position on {name}")
                    continue
                
                logger.info(f"SIGNAL: {name} @ +{peak:.1f}%")
                logger.info(f"KELLY BUY: {mint[:8]}... | {KELLY_BET_SIZE} SOL")
                await buy(mint)'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added duplicate buy prevention")
