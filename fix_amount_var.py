with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Replace 'amount' with 'base_amount' in the buy payload and stats
content = content.replace(
    'payload={"publicKey":str(wallet.pubkey()),"action":"buy","mint":mint,"amount":amount,',
    'payload={"publicKey":str(wallet.pubkey()),"action":"buy","mint":mint,"amount":base_amount,'
)

content = content.replace(
    '"amount":amount,',
    '"amount":base_amount,'
)

content = content.replace(
    'stats["recent_trades"].insert(0,{"type":"BUY","name":name,"bonding":bonding,"amount":amount,"trade_type":trade_type})',
    'stats["recent_trades"].insert(0,{"type":"BUY","name":name,"bonding":bonding,"amount":base_amount,"trade_type":trade_type})'
)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Fixed amount → base_amount")
