with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# REMOVE the old REAL BUY @ PEAK signal watching
old_real_buy = '''                # Check if Bot A bought REAL (peak reached!)
                for sig in real_buy_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"💎 BOT A REAL BUY @ PEAK - SELLING!")
                        await sell(mint, "Real Peak Exit")
                        return
                
                # Check if Bot A KELLY timed out'''

new_test1_sell = '''                # Check if Bot A sold TEST1 (follow the trail exit)
                test1_sell_signals = data.get("test1_sell_signals", [])
                for sig in test1_sell_signals:
                    if sig.get("mint") == mint and time.time() - sig.get("ts", 0) < 30:
                        logger.info(f"📡 BOT A TEST1 SOLD - FOLLOWING!")
                        await sell(mint, "Test1 Exit")
                        return
                
                # Check if Bot A KELLY timed out'''

content = content.replace(old_real_buy, new_test1_sell)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Removed REAL BUY signal, added TEST1 SELL signal")
