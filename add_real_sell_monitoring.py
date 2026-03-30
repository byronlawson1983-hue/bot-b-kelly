with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add REAL SELL signal monitoring after TEST2 SELL
old = '''                # Check if Bot A's TEST2 sold (trail exit)
                test2_sell_signals = data.get("test2_sell_signals", [])
                for sig in test2_sell_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"📡 BOT A TEST2 SOLD - FOLLOWING!")
                        await sell(mint, "Test2 Exit")
                        return'''

new = '''                # Check if Bot A's TEST2 sold (trail exit)
                test2_sell_signals = data.get("test2_sell_signals", [])
                for sig in test2_sell_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"📡 BOT A TEST2 SOLD - FOLLOWING!")
                        await sell(mint, "Test2 Exit")
                        return
                
                # Check if Bot A's REAL sold (trail exit)
                real_sell_signals = data.get("real_sell_signals", [])
                for sig in real_sell_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"📡 BOT A REAL SOLD - FOLLOWING!")
                        await sell(mint, "Real Exit")
                        return'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added REAL SELL signal monitoring")
