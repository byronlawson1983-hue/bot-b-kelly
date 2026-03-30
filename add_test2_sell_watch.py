with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    lines = f.readlines()

# Find the second "test1_sell_signals" block (around line 399-400)
# Add TEST2 sell signal watching after it

insert_text = '''                
                # Check if Bot A's TEST2 sold (trail exit)
                test2_sell_signals = data.get("test2_sell_signals", [])
                for sig in test2_sell_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"📡 BOT A TEST2 SOLD - FOLLOWING!")
                        await sell(mint, "Test2 Exit")
                        return
'''

# Find line 405 (after the duplicate test1_sell block)
for i, line in enumerate(lines):
    if i == 404:  # Insert after line 404 (0-indexed)
        lines.insert(i+1, insert_text)
        break

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.writelines(lines)

print("✅ TEST2 sell signal watching added to Bot B")
