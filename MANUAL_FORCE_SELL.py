from solana.rpc.api import Client
from solders.keypair import Keypair
from solana.rpc.types import TokenAccountOpts
from solders.pubkey import Pubkey
import base58
import requests
from solders.transaction import VersionedTransaction
from solana.rpc.types import TxOpts
from solana.rpc.commitment import Confirmed
import time

PRIVATE_KEY_BYTES = [118,34,43,125,248,155,135,100,236,168,144,20,250,49,12,187,201,82,53,54,115,74,158,55,184,151,254,58,109,248,60,12,170,26,11,205,130,25,112,232,246,229,75,27,36,104,205,162,107,169,240,198,88,88,150,173,67,61,208,95,183,245,39,170]
wallet = Keypair.from_base58_string(base58.b58encode(bytes(PRIVATE_KEY_BYTES)).decode('utf-8'))
rpc = Client("https://mainnet.helius-rpc.com/?api-key=8ba83a2d-8876-4779-ac3d-d8c952ff5c9a")

TOKEN_2022 = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
r = rpc.get_token_accounts_by_owner_json_parsed(wallet.pubkey(), TokenAccountOpts(program_id=TOKEN_2022))

tokens_with_balance = []
for acc in r.value:
    info = acc.account.data.parsed["info"]
    bal = float(info["tokenAmount"]["uiAmount"] or 0)
    if bal > 0:
        tokens_with_balance.append((info["mint"], bal))

print(f"Found {len(tokens_with_balance)} tokens with balance")
print("\nForce selling all tokens...\n")

sold = 0
failed = 0

for mint, bal in tokens_with_balance:
    try:
        payload = {
            "publicKey": str(wallet.pubkey()),
            "action": "sell",
            "mint": mint,
            "amount": "100%",
            "denominatedInSol": "false",
            "slippage": 100,
            "priorityFee": 0.0001,
            "pool": "auto"
        }
        
        resp = requests.post("https://pumpportal.fun/api/trade-local", json=payload, timeout=10)
        
        if resp.status_code == 200:
            tx = VersionedTransaction.from_bytes(resp.content)
            signed = VersionedTransaction(tx.message, [wallet])
            result = rpc.send_transaction(signed, opts=TxOpts(skip_preflight=True, preflight_commitment=Confirmed))
            
            if result.value:
                sig = str(result.value)
                print(f"✅ Sold {mint[:8]}: {sig[:16]}...")
                sold += 1
                time.sleep(0.5)
            else:
                print(f"❌ Failed {mint[:8]}: no signature")
                failed += 1
        else:
            print(f"❌ Failed {mint[:8]}: HTTP {resp.status_code}")
            failed += 1
    except Exception as e:
        print(f"❌ Error {mint[:8]}: {str(e)[:50]}")
        failed += 1

print(f"\n✅ Sold: {sold}")
print(f"❌ Failed: {failed}")

final_balance = rpc.get_balance(wallet.pubkey()).value / 1e9
print(f"\n💰 Final balance: {final_balance:.6f} SOL")
