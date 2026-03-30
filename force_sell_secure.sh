#!/bin/bash
cd /root/bot-b-kelly
ansible-vault decrypt .env --vault-password-file <(echo 'bot-b-secure-vault-2026-v2') --output /tmp/bot_b.env
export $(grep -v '^#' /tmp/bot_b.env | xargs)

python3 << 'PYTHON'
import os, requests
from solders.keypair import Keypair
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solana.rpc.types import TokenAccountOpts
from solders.transaction import VersionedTransaction

PRIVATE_KEY = os.environ['PRIVATE_KEY']
PUBLIC_KEY = os.environ['PUBLIC_KEY']

wallet = Keypair.from_base58_string(PRIVATE_KEY)
client = Client("https://api.mainnet-beta.solana.com")

opts = TokenAccountOpts(program_id=Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"))
resp = client.get_token_accounts_by_owner_json_parsed(Pubkey.from_string(PUBLIC_KEY), opts)

if not resp.value:
    print("No tokens")
    exit()

print(f"Found {len(resp.value)} tokens\n")

for acc in resp.value:
    mint = acc.account.data.parsed['info']['mint']
    try:
        r = requests.post("https://pumpportal.fun/api/trade-local", json={
            "publicKey": PUBLIC_KEY, "action": "sell", "mint": mint,
            "amount": "100%", "denominatedInSol": "false",
            "slippage": 100, "priorityFee": 0.0005, "pool": "pump"
        }, timeout=15)
        if r.status_code == 200:
            tx = VersionedTransaction.from_bytes(r.content)
            signed = VersionedTransaction(tx.message, [wallet])
            from solana.rpc.types import TxOpts
            result = client.send_transaction(signed, opts=TxOpts(skip_preflight=True))
            print(f"✅ Sold {mint[:8]}")
        else:
            print(f"❌ Failed {mint[:8]}")
    except Exception as e:
        print(f"❌ Error {mint[:8]}: {str(e)[:50]}")
PYTHON

rm /tmp/bot_b.env
