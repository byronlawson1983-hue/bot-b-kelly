with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

old = '''                sell_signals = data.get("sell_signals", [])
                
                # Check if Bot A signaled to sell this mint
                for sig in sell_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"🔔 BOT A KELLY SOLD - FOLLOWING!")
                        await sell(mint, "Bot A Exit")
                        return'''

new = '''                sell_signals = data.get("sell_signals", [])
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

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added timeout signal check to Bot B")
