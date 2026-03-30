with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Find the monitoring logic and change it to sell on BUY signals instead of SELL signals
# Current: Watches for "kelly_sell_signals"
# New: Watches for "kelly_buy_signals" and "real_buy_signals"

# This will require finding the signal watching code
print("Current file has kelly_sell_signals references:")
import re
matches = re.findall(r'kelly_sell.*', content)
for m in matches:
    print(f"  {m[:80]}")
    
print("\nSearching for signal monitoring code...")
