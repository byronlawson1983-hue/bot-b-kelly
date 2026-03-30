with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Update monitor to check for BOTH sell signals AND timeout signals
old = '''        # Watch for Bot A's KELLY sell signal
        while time.time() - start_time < p["timeout"]:
            try:
                with open("/tmp/bot_signals.json", "r") as f:
                    data = json.load(f)
                    sell_signals = data.get("sell_signals", [])
                    
                    # Check if Bot A signaled to sell this mint
                    for sig in sell_signals:
                        if sig.get("mint") == mint:
                            logger.info(f"🔔 BOT A KELLY SOLD - FOLLOWING!")
                            await sell(mint, "Bot A Exit")
                            return
            except:
                pass'''

new = '''        # Watch for Bot A's KELLY sell signal OR timeout signal
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
                            return
            except:
                pass'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Bot B will follow Bot A's KELLY timeout signals")
