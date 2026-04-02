#!/bin/bash

python3 << 'EOF'
from solana.rpc.api import Client
from solders.pubkey import Pubkey

bot_a = Pubkey.from_string("9sDwy7UxGE2k2adqnL76GU3Bfd9LsJ5jVwaLJVMHm9Mg")
bot_b = Pubkey.from_string("B1iCUUQkK77DRsW7kzMc11sZvnbQSmXFALDMPNgpvxio")
client = Client("https://api.mainnet-beta.solana.com")

bal_a = client.get_balance(bot_a).value / 1e9
bal_b = client.get_balance(bot_b).value / 1e9

print("=" * 50)
print("BOT BALANCES")
print("=" * 50)
print(f"💰 Bot A: {bal_a:.6f} SOL")
print(f"💰 Bot B: {bal_b:.6f} SOL")
print(f"💰 TOTAL: {bal_a + bal_b:.6f} SOL")
print("=" * 50)
EOF
