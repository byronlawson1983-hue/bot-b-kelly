import os
import requests
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.api import Client
from solana.rpc.types import TxOpts

# Load wallet securely
exec(open('/usr/local/bin/ansible-vault').read())
vault = Vault(os.environ.get('ANSIBLE_VAULT_PASSWORD', 'your-secure-password'))
with open('.env') as f:
    data = vault.load(f.read())
wallet = Keypair.from_base58_string(data['WALLET_PRIVATE_KEY'])

mint = "3JNPaqSF9rXSpoKuek8HaMgwrtzPjByJRZJ8HgqTpump"
amount = 327583420587  # Raw amount with decimals

print(f"Selling BHOURS via Jupiter...")

# Get Jupiter quote
quote_url = f"https://quote-api.jup.ag/v6/quote?inputMint={mint}&outputMint=So11111111111111111111111111111111111111112&amount={amount}&slippageBps=5000"

try:
    quote = requests.get(quote_url, timeout=10).json()
    
    # Get swap transaction
    swap = requests.post("https://quote-api.jup.ag/v6/swap", json={
        "quoteResponse": quote,
        "userPublicKey": str(wallet.pubkey()),
        "wrapAndUnwrapSol": True
    }, timeout=10).json()
    
    # Sign and send
    tx = VersionedTransaction.from_bytes(bytes(swap["swapTransaction"], "base64"))
    tx = VersionedTransaction(tx.message, [wallet])
    
    client = Client("https://api.mainnet-beta.solana.com")
    sig = client.send_raw_transaction(bytes(tx), opts=TxOpts(skip_preflight=True)).value
    
    print(f"✅ Sold! Signature: {sig}")
except Exception as e:
    print(f"❌ Error: {e}")
