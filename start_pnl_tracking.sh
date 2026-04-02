#!/bin/bash

echo "📊 Starting P&L tracking..."

python3 << 'EOF'
from solana.rpc.api import Client
from solders.pubkey import Pubkey
import json
from datetime import datetime

bot_a = Pubkey.from_string("9sDwy7UxGE2k2adqnL76GU3Bfd9LsJ5jVwaLJVMHm9Mg")
bot_b = Pubkey.from_string("B1iCUUQkK77DRsW7kzMc11sZvnbQSmXFALDMPNgpvxio")
client = Client("https://api.mainnet-beta.solana.com")

bal_a = client.get_balance(bot_a).value / 1e9
bal_b = client.get_balance(bot_b).value / 1e9
total = bal_a + bal_b

data = {
    "timestamp": datetime.now().isoformat(),
    "bot_a": bal_a,
    "bot_b": bal_b,
    "total": total
}

with open('/tmp/pnl_start.json', 'w') as f:
    json.dump(data, f)

print(f"✅ Starting balance recorded: {total:.6f} SOL")
print(f"   Bot A: {bal_a:.6f} SOL")
print(f"   Bot B: {bal_b:.6f} SOL")
EOF
