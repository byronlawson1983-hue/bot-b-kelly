import requests
import time
from solders.keypair import Keypair
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solana.rpc.types import TokenAccountOpts
from solders.transaction import VersionedTransaction

PRIVATE_KEY = "386wYrCtvci6sSyf6j448cEVkXVEPsdrzpeAGB5dWtQZjar3D1iJhyQWew2JEprox2ByAMGVzWfdCYWgGqZTPqo9"
PUBLIC_KEY = "EaGvXoxmNFuh3px5bFrYeAwaQungCnWq9LYt91qNYhzK"

wallet = Keypair.from_base58_string(PRIVATE_KEY)
client = Client("https://api.mainnet-beta.solana.com")

opts = TokenAccountOpts(program_id=Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"))
resp = client.get_token_accounts_by_owner_json_parsed(Pubkey.from_string(PUBLIC_KEY), opts)

if not resp.value:
    print("No tokens to sell")
    exit()

print(f"Found {len(resp.value)} tokens\n")

sold = 0
failed = 0

for acc in resp.value:
    mint = acc.account.data.parsed['info']['mint']
    balance = acc.account.data.parsed['info']['tokenAmount']['uiAmount']
    
    payload = {
        "publicKey": PUBLIC_KEY,
        "action": "sell",
        "mint": mint,
        "amount": "100%",
        "denominatedInSol": "false",
        "slippage": 100,
        "priorityFee": 0.0005,
        "pool": "pump"
    }
    
    try:
        r = requests.post("https://pumpportal.fun/api/trade-local", json=payload, timeout=15)
        if r.status_code == 200:
            tx = VersionedTransaction.from_bytes(r.content)
            signed = VersionedTransaction(tx.message, [wallet])
            
            from solana.rpc.types import TxOpts
            result = client.send_transaction(signed, opts=TxOpts(skip_preflight=True))
            
            if result.value:
                print(f"✅ Sold {mint[:8]} ({balance:.0f} tokens): {str(result.value)[:20]}...")
                sold += 1
                time.sleep(1)
            else:
                print(f"❌ Failed {mint[:8]}")
                failed += 1
        else:
            print(f"❌ Failed {mint[:8]}: HTTP {r.status_code}")
            failed += 1
    except Exception as e:
        print(f"❌ Error {mint[:8]}: {str(e)[:80]}")
        failed += 1

print(f"\n✅ Sold: {sold}")
print(f"❌ Failed: {failed}")
print(f"💰 Final balance: {client.get_balance(Pubkey.from_string(PUBLIC_KEY)).value / 1e9} SOL")
