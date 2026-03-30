with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Find where we check for KELLY BUY signal and add KELLY timeout check
old_code = '''                # Check if Bot A bought KELLY (peak signal)
                kelly_buy_signals = data.get("kelly_buy_signals", [])
                for sig in kelly_buy_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"💎 BOT A KELLY BUY @ PEAK - SELLING!")
                        await sell(mint, "Kelly Peak Exit")
                        return'''

new_code = '''                # Check if Bot A bought KELLY (peak signal)
                kelly_buy_signals = data.get("kelly_buy_signals", [])
                for sig in kelly_buy_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"💎 BOT A KELLY BUY @ PEAK - SELLING!")
                        await sell(mint, "Kelly Peak Exit")
                        return
                
                # Check if Bot A's KELLY timed out
                kelly_timeout_signals = data.get("kelly_timeout_signals", [])
                for sig in kelly_timeout_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"⏰ BOT A KELLY TIMEOUT - SELLING!")
                        await sell(mint, "Kelly Timeout Exit")
                        return'''

content = content.replace(old_code, new_code)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added KELLY timeout signal watching")
