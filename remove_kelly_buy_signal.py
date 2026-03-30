with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# REMOVE the KELLY BUY @ PEAK signal watching
old_kelly = '''                # Check if Bot A bought KELLY (peak reached!)
                for sig in kelly_buy_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"💎 BOT A KELLY BUY @ PEAK - SELLING!")
                        await sell(mint, "Kelly Peak Exit")
                        return
                
                # Check if Bot A sold TEST1'''

new_test1 = '''                # Check if Bot A sold TEST1'''

content = content.replace(old_kelly, new_test1)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Removed KELLY BUY @ PEAK signal watching")
