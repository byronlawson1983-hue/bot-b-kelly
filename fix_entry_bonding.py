with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Find where signal buy happens - it passes bonding=0
# Need to get CURRENT bonding from websocket data BEFORE buying
old = '''                result = await buy(mint, signal['name'], 0, 0, "")'''

new = '''                # Get current bonding from latest_data if available
                current_bonding = latest_data.get(mint, {}).get('progress', 0)
                result = await buy(mint, signal['name'], current_bonding, 0, "")'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Fixed entry_bonding - now gets current bonding % from websocket")
