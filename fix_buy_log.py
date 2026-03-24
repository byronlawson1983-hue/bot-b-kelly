with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Find the buy log and change TEST1 to KELLY
content = content.replace(
    'logger.info(f"💰 TEST1 BUY: {name} @ {bonding}% | {amount:.6f} SOL")',
    'logger.info(f"💰 KELLY BUY: {name} @ {bonding}% | {amount:.6f} SOL")'
)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Fixed buy log to say KELLY instead of TEST1")
