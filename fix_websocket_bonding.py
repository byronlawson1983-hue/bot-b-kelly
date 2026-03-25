with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add bonding curve % to websocket data
old = '''                            latest_data[mint] = {
                                'mint': mint,
                                'marketCapSol': mc,
                                'name': d.get('name', mint[:8]),
                            }'''

new = '''                            bonding = d.get('progress', 0)  # Get bonding curve %
                            latest_data[mint] = {
                                'mint': mint,
                                'marketCapSol': mc,
                                'progress': bonding,  # Store bonding curve %
                                'name': d.get('name', mint[:8]),
                            }'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Websocket now stores bonding curve %!")
