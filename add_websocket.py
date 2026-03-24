# Read Bot A's websocket code
with open("/root/bot-a-test1/PYTHON_BOT_FROZEN_DO_NOT_TOUCH.py", "r") as f:
    bot_a = f.read()

# Extract the websocket subscription function from Bot A
import re
subscribe_match = re.search(r'(async def subscribe_to_token.*?(?=\nasync def |\n\n))', bot_a, re.DOTALL)
if subscribe_match:
    websocket_code = subscribe_match.group(1)
    
    # Read Bot B
    with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
        bot_b = f.read()
    
    # Replace Bot B's stub subscribe_to_token with Bot A's real one
    bot_b = re.sub(r'async def subscribe_to_token\(mint\):.*?pass', websocket_code, bot_b, flags=re.DOTALL)
    
    with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
        f.write(bot_b)
    
    print("✅ Copied Bot A's websocket to Bot B")
else:
    print("❌ Could not find subscribe_to_token in Bot A")
