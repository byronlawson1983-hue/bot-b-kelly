with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add debug logging in the websocket reader
old = '''                    async for msg in ws_global:
                        try:
                            d = json.loads(msg)
                            mint = d.get('mint')
                            if not mint:
                                continue'''

new = '''                    async for msg in ws_global:
                        try:
                            d = json.loads(msg)
                            mint = d.get('mint')
                            logger.debug(f"📨 WS MSG: {mint[:8] if mint else 'no-mint'}")
                            if not mint:
                                continue'''

content = content.replace(old, new)

# Also add logging when updating latest_data
old2 = '''                            latest_data[mint] = {
                                'mint': mint,
                                'marketCapSol': mc,
                                'name': d.get('name', mint[:8]),
                                'progress': bonding,
                                'vSol': v_sol,
                                'vTokens': d.get('vTokensInBondingCurve', 1)
                            }'''

new2 = '''                            latest_data[mint] = {
                                'mint': mint,
                                'marketCapSol': mc,
                                'name': d.get('name', mint[:8]),
                                'progress': bonding,
                                'vSol': v_sol,
                                'vTokens': d.get('vTokensInBondingCurve', 1)
                            }
                            logger.debug(f"💾 Updated latest_data for {mint[:8]}: MC={mc:.4f}")'''

content = content.replace(old2, new2)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added debug logging")
