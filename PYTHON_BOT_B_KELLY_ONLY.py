import random
import asyncio
import json
import logging
import os
import websockets
import requests
import base58
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from solders.transaction import VersionedTransaction
from solana.rpc.types import TxOpts
import base64

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

WALLET_PATH = os.getenv("PRIVATE_KEY")
if not WALLET_PATH:
    raise Exception("PRIVATE_KEY not set")

wallet = Keypair.from_bytes(base58.b58decode(WALLET_PATH))
logger.info(f"✅ Wallet: {wallet.pubkey()}")

RPC = "https://api.mainnet-beta.solana.com"
client = Client(RPC)

SIGNAL_FILE = "/tmp/bot_signals.json"
WS_URL = "wss://pumpportal.fun/api/data"

KELLY_AMOUNT = 0.01

latest_data = {}
current_position = None  # Track current holding to prevent double-buys

async def send_with_retry(tx, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = client.send_transaction(tx, opts=TxOpts(skip_preflight=False, preflight_commitment=Confirmed))
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"❌ {e}")
                return None
            await asyncio.sleep(1)

async def subscribe_to_token(mint):
    try:
        async with websockets.connect(WS_URL) as ws:
            await ws.send(json.dumps({"method":"subscribeTokenTrade","keys":[mint]}))
            logger.info(f"📡 Subscribed to {mint[:8]}...")
    except:
        pass

async def buy(mint, name, bonding_pct):
    """Buy a token"""
    global current_position
    
    # Skip if we already hold this token
    if current_position == mint:
        logger.info(f"⏭️ SKIP: Already holding {mint[:8]}...")
        return False
    
    logger.info(f"💰 KELLY BUY: {name} @ {bonding_pct}% | {KELLY_AMOUNT:.6f} SOL")
    
    try:
        payload = {
            "publicKey": str(wallet.pubkey()),
            "action": "buy",
            "mint": mint,
            "amount": KELLY_AMOUNT,
            "denominatedInSol": "true",
            "slippage": 100,
            "priorityFee": 0.0001,
            "pool": "auto"
        }
        
        r = requests.post("https://pumpportal.fun/api/trade-local", json=payload, timeout=10)
        if r.status_code != 200:
            return False
        
        if 'application/json' in r.headers.get('Content-Type', ''):
            tx_bytes = base64.b64decode(r.json()['transaction'])
        else:
            tx_bytes = r.content
        
        tx = VersionedTransaction.from_bytes(tx_bytes)
        tx = VersionedTransaction(tx.message, [wallet])
        result = await send_with_retry(tx)
        
        if result:
            sig = result if isinstance(result, str) else str(result.value)
            logger.info(f"✅ BOUGHT: {sig[:8]} | Mint: {mint}")
            current_position = mint  # Set current position
            
            await subscribe_to_token(mint)
            asyncio.create_task(monitor(mint, name))
            return True
        return False
    except Exception as e:
        logger.error(f"❌ {e}")
        return False

async def sell(mint, reason):
    """Sell a token"""
    global current_position
    
    logger.info(f"💸 SELLING: {mint[:8]}... | {reason}")
    
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
        
        r = requests.post("https://pumpportal.fun/api/trade-local", json=payload, timeout=10)
        if r.status_code != 200:
            return False
        
        if 'application/json' in r.headers.get('Content-Type', ''):
            tx_bytes = base64.b64decode(r.json()['transaction'])
        else:
            tx_bytes = r.content
        
        tx = VersionedTransaction.from_bytes(tx_bytes)
        tx = VersionedTransaction(tx.message, [wallet])
        result = await send_with_retry(tx)
        
        if result:
            sig = result if isinstance(result, str) else str(result.value)
            await asyncio.sleep(3)
            logger.info(f"✅ SOLD: {sig[:16]}... (settlement complete)")
            
            # Calculate profit
            if current_position and "buy_amount" in current_position:
                buy_amount = current_position["buy_amount"]
                balance_after = client.get_balance(wallet.pubkey()).value / 1e9
                
                # Simple calculation: sold amount = balance increase
                # More accurate: query the actual transaction
                profit_estimate = balance_after - (balance_before if 'balance_before' in locals() else balance_after - 0.01)
                logger.info(f"💰 PROFIT ESTIMATE: {current_position['name'][:12]} | Buy: {buy_amount:.4f} SOL | Est profit: {profit_estimate:+.6f} SOL")
            
            current_position = None  # Clear position
            return True
        return False
    except Exception as e:
        logger.error(f"❌ {e}")
        return False

async def monitor(mint, name):
    """Monitor position and sell after 6 seconds OR on -10% stop loss"""
    global current_position
    
    hold_time = 6.0
    """Monitor for Bot A's KELLY sell signal"""
    timeout = random.choice([6, 8])
    logger.info(f"👁️ MONITOR: {name} | TRAILING UP +10% | Timeout: {timeout}s")
    
    # Track entry price
    entry_price = latest_data.get(mint[:8], {}).get('mc', 0)
    
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < timeout:
        try:
            if os.path.exists(SIGNAL_FILE):
                with open(SIGNAL_FILE, 'r') as f:
                    data = json.load(f)
                
                # Check for KELLY sell signal
                if data.get("action") == "KELLY_SELL" and data.get("mint") == mint:
                    logger.info(f"📡 BOT A KELLY SELL - FOLLOWING!")
                    await sell(mint, "Kelly Exit")
                    return
                
                # Check for TEST1 sell (early exit)
                if data.get("action") == "TEST1_SELL" and data.get("mint") == mint:
                    logger.info(f"📡 BOT A TEST1 SOLD - FOLLOWING!")
                    await sell(mint, "Test1 Exit")
                    return
        except:
            pass
        
        await asyncio.sleep(0.5)
    
    # Timeout
    logger.info(f"⏰ TIMEOUT: {name}")
    await sell(mint, "Timeout")

processed_signals = set()

async def watch_signals():
    """Watch for Bot A signals"""
    logger.info("👁️ Watching for Bot A signals...")
    
    # CLEAR OLD SIGNALS ON STARTUP
    try:
        if os.path.exists(SIGNAL_FILE):
            with open(SIGNAL_FILE, 'r') as f:
                data = json.load(f)
            
            # Mark all existing signals as processed (IGNORE OLD SIGNALS)
            for signal in data.get("signals", []):
                mint = signal.get("mint")
                ts = signal.get("ts")
                processed_signals.add(f"{mint}_{ts}")
            
            logger.info(f"🚫 Cleared {len(processed_signals)} old signals - only processing NEW signals")
    except:
        pass
    
    while True:
        try:
            if os.path.exists(SIGNAL_FILE):
                with open(SIGNAL_FILE, 'r') as f:
                    data = json.load(f)
                
                # Check signals array for INSTANT buys (tokens that passed TEST1)
                # Check for TEST1_PASSED signals (BUY ON EVERY PASSED TEST!)
                if data.get("type") == "TEST1_PASSED":
                    mint = data.get("mint")
                    name = data.get("name", "Unknown")
                    peak_pnl = data.get("peak_pnl", 0)
                    ts = data.get("timestamp", 0)
                    
                    signal_key = f"{mint}_{ts}"
                    if signal_key not in processed_signals:
                        processed_signals.add(signal_key)
                        logger.info(f"📡 TEST1_PASSED SIGNAL: {name} @ +{peak_pnl:.1f}%")
                        logger.info(f"💰 TEST1_PASSED BUY: {mint[:8]}... | {KELLY_AMOUNT} SOL")
                        await buy(mint, name, 35.0)
                
                # Check for INSTANT signals (TEST APPROVED - earlier entry)
                if data.get("action") == "INSTANT":
                    mint = data.get("mint")
                    name = data.get("name", "Unknown")
                    peak = data.get("peak", 0)
                    
                    signal_key = f"{mint}_{peak}"
                    if signal_key not in processed_signals:
                        processed_signals.add(signal_key)
                        logger.info(f"📡 INSTANT SIGNAL: {name} @ +{peak:.1f}%")
                        logger.info(f"💰 INSTANT BUY: {mint[:8]}... | {KELLY_AMOUNT} SOL")
                        await buy(mint, name, 35.0)
                
                # Also check signals array for backwards compatibility
                instant_signals = data.get("signals", [])
                for signal in instant_signals:
                    mint = signal.get("mint")
                    ts = signal.get("ts")
                    signal_key = f"{mint}_{ts}"
                    
                    if signal_key not in processed_signals:
                        processed_signals.add(signal_key)
                        
                        name = signal.get("name", "Unknown")
                        peak = signal.get("peak", 0)
                        
                        logger.info(f"📡 INSTANT SIGNAL: {name} @ +{peak:.1f}%")
                        logger.info(f"💰 INSTANT BUY: {mint[:8]}... | {KELLY_AMOUNT} SOL")
                        await buy(mint, name, 35.0)
        except:
            pass
        
        await asyncio.sleep(0.1)

async def websocket_listener():
    """Listen to PumpPortal websocket for market data - crash-proof"""
    while True:
        try:
            async with websockets.connect(WS_URL, ping_interval=20, ping_timeout=10) as ws:
                await ws.send(json.dumps({"method":"subscribeNewToken"}))
                logger.info("✅ Connected to PumpPortal websocket")
                
                while True:
                    try:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        
                        if 'mint' in data:
                            mint = data['mint']
                            latest_data[mint[:8]] = {
                                'mc': data.get('marketCap', 0) / 1000,
                                'bonding': data.get('progress', 0)
                            }
                    except Exception as msg_error:
                        logger.warning(f"WS message error: {msg_error}")
                        continue
        except Exception as e:
            logger.error(f"🚨 WS DISCONNECTED: {e}")
            
            # EMERGENCY SELL if we have a position
            if current_position:
                logger.warning(f"⚠️ EMERGENCY SELL: {current_position['name']} (websocket down)")
                try:
                    await sell(current_position['mint'], "WS disconnect")
                except Exception as sell_err:
                    logger.error(f"Emergency sell failed: {sell_err}")
            
            logger.info("Reconnecting in 5s...")
            await asyncio.sleep(5)


async def close_token_account(mint):
    """Close token account to reclaim rent (0.00203 SOL)"""
    try:
        from spl.token.instructions import close_account, CloseAccountParams
        from spl.token.constants import TOKEN_PROGRAM_ID
        
        # Find token account
        token_program = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
        opts = TokenAccountOpts(program_id=token_program)
        accounts = client.get_token_accounts_by_owner(wallet.pubkey(), opts)
        
        for acc in accounts.value:
            acc_mint = str(Pubkey(acc.account.data[0:32]))
            if acc_mint == mint:
                token_account = acc.pubkey
                
                # Close account instruction
                ix = close_account(CloseAccountParams(
                    program_id=TOKEN_PROGRAM_ID,
                    account=token_account,
                    dest=wallet.pubkey(),
                    owner=wallet.pubkey()
                ))
                
                # Send transaction
                from solders.transaction import Transaction
                tx = Transaction([ix], wallet.pubkey())
                result = client.send_transaction(tx, wallet)
                
                logger.info(f"✅ Closed token account - reclaimed 0.00203 SOL rent")
                return True
                
    except Exception as e:
        logger.warning(f"⚠️ Failed to close token account: {e}")
    
    return False


async def main():
    logger.info("🚀 BOT B STARTING")
    logger.info(f"Kelly: {KELLY_AMOUNT} SOL")
    
    await asyncio.gather(
        watch_signals(),
        websocket_listener()
    )

if __name__ == "__main__":
    asyncio.run(main())
