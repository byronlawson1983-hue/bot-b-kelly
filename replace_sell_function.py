with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Find and replace the entire sell function with Bot A's working version
import re

# Remove old sell function
pattern = r'async def sell\(.*?\n(?:.*?\n)*?(?=\nasync def |$)'
content = re.sub(pattern, '', content, count=1)

# Add Bot A's working sell function
new_sell = '''async def sell(mint, reason, position_data=None):
    """PumpPortal sell - same as Bot A"""
    import requests
    from solders.transaction import VersionedTransaction
    
    logger.info(f"💸 SELLING: {mint[:8]}... | {reason}")
    
    # PumpPortal sell
    try:
        logger.info("🔧 PumpPortal sell")
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
            
            result = await asyncio.to_thread(
                rpc_client.send_transaction, signed
            )
            
            if result.value:
                sig = str(result.value)
                logger.info(f"📤 Sell submitted: {sig[:16]}... waiting 5s for settlement")
                await asyncio.sleep(5)
                logger.info(f"✅ SOLD: {sig[:16]}... (settlement complete)")
                return True
        
        logger.error("❌ PumpPortal sell failed")
        return False
        
    except Exception as e:
        logger.error(f"❌ Sell error: {e}")
        return False

'''

# Insert before monitor function
content = content.replace('async def monitor(', new_sell + 'async def monitor(')

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Replaced sell() with Bot A's working version")
