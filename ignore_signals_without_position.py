with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add check to ignore sell signals if we don't have a position
old = '''                # Check if Bot A sold TEST1 (follow the trail exit)
                test1_sell_signals = data.get("test1_sell_signals", [])
                for sig in test1_sell_signals:
                    if sig.get("mint") == mint and time.time() - sig.get("ts", 0) < 30:
                        logger.info(f"📡 BOT A TEST1 SOLD - FOLLOWING!")
                        await sell(mint, "Test1 Exit")
                        return'''

new = '''                # Check if we still have a position before acting on signals
                if not current_position or current_position.get("mint") != mint:
                    logger.info(f"⚠️ No position on {mint[:8]}... - ignoring signals")
                    return
                
                # Check if Bot A sold TEST1 (follow the trail exit)
                test1_sell_signals = data.get("test1_sell_signals", [])
                for sig in test1_sell_signals:
                    if sig.get("mint") == mint and time.time() - sig.get("ts", 0) < 30:
                        logger.info(f"📡 BOT A TEST1 SOLD - FOLLOWING!")
                        await sell(mint, "Test1 Exit")
                        return'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added position check before processing sell signals")
