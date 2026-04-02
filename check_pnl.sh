#!/bin/bash

python3 << 'EOF'
from solana.rpc.api import Client
from solders.pubkey import Pubkey
import json
import os

if not os.path.exists('/tmp/pnl_start.json'):
    print("❌ No starting balance recorded! Run ./start_pnl_tracking.sh first")
    exit(1)

with open('/tmp/pnl_start.json', 'r') as f:
    start = json.load(f)

bot_a = Pubkey.from_string("9sDwy7UxGE2k2adqnL76GU3Bfd9LsJ5jVwaLJVMHm9Mg")
bot_b = Pubkey.from_string("B1iCUUQkK77DRsW7kzMc11sZvnbQSmXFALDMPNgpvxio")
client = Client("https://api.mainnet-beta.solana.com")

bal_a = client.get_balance(bot_a).value / 1e9
bal_b = client.get_balance(bot_b).value / 1e9
total = bal_a + bal_b

pnl = total - start['total']
pnl_pct = (pnl / start['total']) * 100

print("=" * 60)
print("📊 P&L REPORT")
print("=" * 60)
print(f"Starting: {start['total']:.6f} SOL")
print(f"Current:  {total:.6f} SOL")
print(f"P&L:      {pnl:+.6f} SOL ({pnl_pct:+.2f}%)")
print("=" * 60)
print(f"Bot A: {start['bot_a']:.6f} → {bal_a:.6f} ({bal_a - start['bot_a']:+.6f})")
print(f"Bot B: {start['bot_b']:.6f} → {bal_b:.6f} ({bal_b - start['bot_b']:+.6f})")
print("=" * 60)
EOF
