with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Replace the monitor function to watch for BUY signals instead of SELL signals
old_monitor = '''    # Watch for Bot A's KELLY sell signal
    while time.time() - start_time < p["timeout"]:
        try:
            with open("/tmp/bot_signals.json", "r") as f:
                data = json.load(f)
                sell_signals = data.get("sell_signals", [])
                timeout_signals = data.get("timeout_signals", [])
                
                # Check if Bot A signaled to sell this mint
                for sig in sell_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"🔔 BOT A KELLY SOLD - FOLLOWING!")
                        await sell(mint, "Bot A Exit")
                        return
                
                # Check if Bot A's KELLY timed out
                for sig in timeout_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"⏱️ BOT A KELLY TIMEOUT - FOLLOWING!")
                        await sell(mint, "Bot A Timeout")
                        return'''

new_monitor = '''    # Watch for Bot A's KELLY/REAL BUY signals (exit at peak!)
    while time.time() - start_time < p["timeout"]:
        try:
            with open("/tmp/bot_signals.json", "r") as f:
                data = json.load(f)
                kelly_buy_signals = data.get("kelly_buy_signals", [])
                real_buy_signals = data.get("real_buy_signals", [])
                test2_fail_signals = data.get("test2_fail_signals", [])
                
                # Check if Bot A bought KELLY (peak reached!)
                for sig in kelly_buy_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"💎 BOT A KELLY BUY @ PEAK - SELLING!")
                        await sell(mint, "Kelly Peak Exit")
                        return
                
                # Check if Bot A bought REAL (peak reached!)
                for sig in real_buy_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"💎 BOT A REAL BUY @ PEAK - SELLING!")
                        await sell(mint, "Real Peak Exit")
                        return
                
                # Check if Bot A's TEST2 failed (abort!)
                for sig in test2_fail_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"⚠️ BOT A TEST2 FAILED - ABORTING!")
                        await sell(mint, "Test2 Abort")
                        return'''

content = content.replace(old_monitor, new_monitor)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Changed Bot B to sell on KELLY/REAL BUY signals + TEST2 fail abort")
