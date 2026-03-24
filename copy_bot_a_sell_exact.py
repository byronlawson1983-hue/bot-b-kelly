# Read Bot A's exact sell function
with open("/root/bot-a-test1/PYTHON_BOT_FROZEN_DO_NOT_TOUCH.py", "r") as f:
    bot_a = f.read()

# Extract sell function from Bot A
import re
sell_match = re.search(r'(async def sell\(.*?\n(?:.*?\n)*?)(?=\nasync def |\nif __name__)', bot_a, re.DOTALL)
bot_a_sell = sell_match.group(1) if sell_match else ""

# Read Bot B
with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    bot_b = f.read()

# Remove Bot B's sell function
bot_b = re.sub(r'async def sell\(.*?\n(?:.*?\n)*?(?=\nasync def |$)', '', bot_b, count=1)

# Insert Bot A's sell before monitor
bot_b = bot_b.replace('async def monitor(', bot_a_sell + '\nasync def monitor(')

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(bot_b)

print("✅ Copied Bot A's EXACT sell function to Bot B")
