import requests
from solders.keypair import Keypair
from solana.rpc.api import Client

# NEW Bot B wallet
PRIVATE_KEY = "386wYrCtvci6sSyf6j448cEVkXVEPsdrzpeAGB5dWtQZjar3D1iJhyQWew2JEprox2ByAMGVzWfdCYWgGqZTPqo9"
PUBLIC_KEY = "EaGvXoxmNFuh3px5bFrYeAwaQungCnWq9LYt91qNYhzK"

wallet = Keypair.from_base58_string(PRIVATE_KEY)
client = Client("https://api.mainnet-beta.solana.com")

from solders.pubkey import Pubkey
from solana.rpc.types import TokenAccountOpts

opts = TokenAccountOpts(program_id=Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"))
resp = client.get_token_accounts_by_owner(Pubkey.from_string(PUBLIC_KEY), opts)

if not resp.value:
    print("No tokens to sell")
    exit()

print(f"Found {len(resp.value)} tokens\n")

for i, acc in enumerate(resp.value):
    mint = str(acc.account.data.parsed['info']['mint'])
    
    payload = {
        "publicKey": PUBLIC_KEY,
        "action": "sell",
        "mint": mint,
        "amount": "100%",
        "denominatedInSol": "false",
        "slippage": 100,
        "priorityFee": 0.0001,
        "pool": "auto"
    }
    
    try:
        r = requests.post("https://pumpportal.fun/api/trade-local", json=payload, timeout=10)
        if r.status_code == 200:
            from solders.transaction import VersionedTransaction
            tx = VersionedTransaction.from_bytes(r.content)
            signed = VersionedTransaction(tx.message, [wallet])
            result = client.send_transaction(signed)
            print(f"✅ Sold {mint[:8]}: {str(result.value)[:20]}...")
        else:
            print(f"❌ Failed {mint[:8]}")
    except Exception as e:
        print(f"❌ Error {mint[:8]}: {e}")

print(f"\n💰 Final balance: {client.get_balance(Pubkey.from_string(PUBLIC_KEY)).value / 1e9} SOL")
