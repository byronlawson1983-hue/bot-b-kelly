#!/bin/bash
cd /root/bot-b-kelly

ansible-vault decrypt .env --vault-password-file <(echo 'bot-b-secure-vault-2026') --output /tmp/bot_b_env.env
export $(grep -v '^#' /tmp/bot_b_env.env | xargs)
rm /tmp/bot_b_env.env

python3 << 'EOF'
import requests
import base58
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solana.rpc.types import TokenAccountOpts
from solders.transaction import VersionedTransaction
from solana.rpc.types import TxOpts
from solana.rpc.commitment import Confirmed
import os

wallet = Keypair.from_bytes(base58.b58decode(os.getenv("PRIVATE_KEY")))
client = Client("https://api.mainnet-beta.solana.com")

print("Checking for tokens to sell...")

token_program = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
opts = TokenAccountOpts(program_id=token_program)
response = client.get_token_accounts_by_owner(wallet.pubkey(), opts)

sold = 0
for acc in response.value:
    amount = int.from_bytes(acc.account.data[64:72], 'little')
    if amount > 0:
        mint = str(Pubkey(acc.account.data[0:32]))
        
        try:
            payload = {
                "publicKey": str(wallet.pubkey()),
                "action": "sell",
                "mint": mint,
                "amount": "100%",
                "denominatedInSol": "false",
                "slippage": 100,
                "priorityFee": 0.001,
                "pool": "auto"
            }
            
            r = requests.post("https://pumpportal.fun/api/trade-local", json=payload, timeout=10)
            if r.status_code == 200:
                import base64
                if 'application/json' in r.headers.get('Content-Type', ''):
                    tx_bytes = base64.b64decode(r.json()['transaction'])
                else:
                    tx_bytes = r.content
                
                tx = VersionedTransaction.from_bytes(tx_bytes)
                tx = VersionedTransaction(tx.message, [wallet])
                result = client.send_transaction(tx, opts=TxOpts(skip_preflight=True, preflight_commitment=Confirmed))
                
                if result.value:
                    print(f"✅ Sold {mint[:8]}")
                    sold += 1
        except Exception as e:
            print(f"❌ {mint[:8]}: {e}")

print(f"\n✅ Force sell complete: {sold} tokens sold")
EOF
