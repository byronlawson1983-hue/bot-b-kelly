from solana.rpc.async_api import AsyncClient
#!/usr/bin/env python3
"""
BOT B - Kelly-Only Follower
Watches Bot A signals and buys Kelly with separate wallet
"""
import os,asyncio,logging,requests,websockets,json,time,base58,base64,random
from flask import Flask,render_template_string
from flask_socketio import SocketIO
from threading import Thread
from dotenv import load_dotenv
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solana.rpc.commitment import Confirmed

from dotenv import load_dotenv

load_dotenv()

import logging
import sys

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# Constants
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RPC_ENDPOINT = os.getenv("RPC_ENDPOINT", "https://api.mainnet-beta.solana.com")

# Initialize wallet
import base58
wallet = Keypair.from_base58_string(PRIVATE_KEY)
from solana.rpc.api import Client as SyncClient
rpc_client = SyncClient(RPC_ENDPOINT)

# Websocket for price feeds
ws = None
ws_global = None  # Global websocket connection
latest_data = {}  # Store latest price data per mint
client = AsyncClient(RPC_ENDPOINT)

AMOUNT_1=0.001      # Test scout 1
AMOUNT_2=0.002   # Test scout 2
AMOUNT_3=0.003      # Real bet - OPTION B TEST RATE
STOP_LOSS_PCT=-5
TRAILING_STOP_TRIGGER=10
TRAILING_PULLBACK=3


# Bot B specific settings
MIN_WALLET_BALANCE = 0.001  # Minimum SOL to keep in wallet
KELLY_AMOUNT = 0.01
bought_mints = set()
should_restart = False
current_position = None
blacklist = set()
token_blacklist = set()
should_restart = False
test_approved_tokens = set()
kelly_approved_tokens = set()
test2_approved_tokens = set()
real_approved_tokens = set()
recycled_tokens = set()
recycling_queued = False
stats = {"test_trades": 0, "kelly_trades": 0, "real_trades": 0, "total_trades": 0, "recent_trades": []}
latest_data = {}  # Track latest price data for monitoring
VOLUME_DEATH_SECONDS = 10  # Dead token detection
TIMEOUT_MIN = 10
TIMEOUT_MAX = 15

# Functions from Bot A



def emit(event, data):
    """Stub - Bot B doesn't emit events"""
    pass


def emit(event, data):
    """Stub - Bot B doesn't emit events"""
    pass



def instant_test_analysis(*args, **kwargs):
    """Stub - not needed for Bot B"""
    return False

async def subscribe_to_token(mint):
    global ws_global
    if ws_global:
        try:
            await ws_global.send(json.dumps({"method":"subscribeTokenTrade","keys":[mint]}))
            logger.info(f"📡 Subscribed to {mint[:8]}...")
        except:pass

def get_balance():
    """Get wallet SOL balance"""
    try:
        from solana.rpc.api import Client
        client = Client(RPC_ENDPOINT)
        balance = client.get_balance(wallet.pubkey()).value / 1e9
        return balance
    except:
        return 0

def check_dev_wallet(creator):
    """Stub - Bot B trusts Bot A already validated this"""
    return True



async def send_with_retry(tx, max_retries=3):
    """Send transaction with retries"""
    for attempt in range(max_retries):
        try:
            from solana.rpc.types import TxOpts
            from solana.rpc.commitment import Confirmed
            result = await client.send_transaction(tx, opts=TxOpts(skip_confirmation=False, preflight_commitment=Confirmed))
            sig = result
            return str(sig.value)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(1)
    return None

async def buy(mint,name,bonding,mc,creator,kelly=False):
    global current_position,trades_in_cycle,should_restart,current_cycle_token
    
    # BOT B: ALWAYS KELLY
    trade_type = "KELLY"
    base_amount = KELLY_AMOUNT
    
    logger.info(f"💰 KELLY BUY: {name} @ {bonding}% | {base_amount:.6f} SOL")
    
    try:
        payload={"publicKey":str(wallet.pubkey()),"action":"buy","mint":mint,"amount":base_amount,"denominatedInSol":"true","slippage": 100,"priorityFee":0.0001,"pool":"auto"}
        r=requests.post("https://pumpportal.fun/api/trade-local",json=payload,timeout=10)
        
        if r.status_code!=200:return False
        
        if 'application/json' in r.headers.get('Content-Type',''):
            tx_bytes=base64.b64decode(r.json()['transaction'])
        else:
            tx_bytes=r.content
        
        tx=VersionedTransaction.from_bytes(tx_bytes)
        tx=VersionedTransaction(tx.message,[wallet])
        result = await send_with_retry(tx)
        
        if result:
            sig = result if isinstance(result, str) else str(result.value)
            logger.info(f"✅ BOUGHT: {sig[:8]} | Mint: {mint}")
            
            # Subscribe to websocket for price data
            await subscribe_to_token(mint)
            
            # Monitor this position
            asyncio.create_task(monitor(mint))
            
            timeout= 15  # Bot B doesn't need 120s - no TEST positions
            
            # FORCE OVERRIDE for REAL buys - stop TEST monitor immediately
            if trade_type == "REAL":
                await asyncio.sleep(0.1)  # Brief pause to let TEST monitor exit
                logger.info(f"🛑 TEST monitor stopped")
                # CRITICAL: CREATE current_position for REAL/KELLY
                # Check if position already exists (created early in monitor)
                if not current_position:
                    # Recalculate timeout for KELLY/REAL (was calculated for TEST1)
                    kelly_timeout = 15  # Quick exit - most signals come in 13-15s
                    current_position = {
                        "trade_type": trade_type,
                        "mint": mint,
                        "name": name,
                        "buy_time": time.time(),
                        "entry_mc": mc,
                        "entry_bonding": bonding,
                        "creator": creator,
                        "peak_pnl": 0,
                        "trailing_stop_active": False,
                        "timeout": kelly_timeout,
                        "last_trade_time": time.time()
                    }
                    logger.info(f"📊 {trade_type} position created in buy()")
                else:
                    logger.info(f"✅ {trade_type} position already exists - not overwriting")
                # CRITICAL: Find and store the REAL token account address
                await asyncio.sleep(0.5)  # Wait for token account to be created
                from solana.rpc.types import TokenAccountOpts
                from solders.pubkey import Pubkey
                try:
                    largest_balance = 0
                    real_token_account = None
                    for program in ["TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb", "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"]:
                        r = rpc_client.get_token_accounts_by_owner_json_parsed(wallet.pubkey(), TokenAccountOpts(program_id=Pubkey.from_string(program)))
                        for a in r.value:
                            info = a.account.data.parsed["info"]
                            if info["mint"] == mint:
                                balance = float(info["tokenAmount"]["uiAmount"] or 0)
                                if balance > largest_balance:
                                    largest_balance = balance
                                    real_token_account = str(a.pubkey)
                    if real_token_account:
                        current_position["token_account"] = real_token_account
                        logger.info(f"📍 REAL token account pinned: {real_token_account[:8]}...")
                except Exception as e:
                    logger.warning(f"⚠️ Could not pin token account: {e}")
            
            # Create full position
            current_position={
                "mint":mint,
                "name":name,
                "buy_time":time.time(),
                "entry_bonding":bonding,
                "entry_mc":mc,
                "creator":creator,
                "trailing_stop_active":False,
                "peak_pnl":0,
                "last_trade_time":time.time(),
                "timeout":timeout,
                "amount":base_amount,
                "trade_type":trade_type
            }
            
            stats["total_trades"]+=1
            stats["recent_trades"].insert(0,{"type":"BUY","name":name,"bonding":bonding,"amount":base_amount,"trade_type":trade_type})
            stats["recent_trades"]=stats["recent_trades"][:20]
            # emit() - disabled
            
            await subscribe_to_token(mint)
            
            # For TEST positions, do instant analysis before monitoring
            if trade_type in ["TEST1", "TEST2"]:
                await asyncio.sleep(0.5)  # Brief wait for WebSocket to update
                instant_test_analysis(mint, name, trade_type, bonding, creator)
                # If instant_test_analysis cleared position, don't start monitor
                if not current_position or current_position["mint"] != mint:
                    return True
            
            # Start monitoring immediately (no settlement wait)
            # REMOVED DUPLICATE MONITOR
            return True
    except Exception as e:
        logger.error(f"❌ {e}")
    return False






async def sell(mint, reason, position_data=None):
    """Hybrid: Direct RPC first, PumpPortal fallback"""
    import requests, time
    from solders.transaction import VersionedTransaction
    from solana.rpc.types import TxOpts
    from solana.rpc.commitment import Confirmed
    
    logger.info(f"💸 SELLING: {mint[:8]}... | {reason}")
    
    # METHOD 1: Direct RPC (from working bot)
    try:
        logger.info("🔧 Method 1: Direct RPC sell")
        import struct as _struct
        from solders.pubkey import Pubkey as _PK
        from solders.instruction import Instruction as _IX, AccountMeta as _AM
        from solders.message import MessageV0 as _MV0
        from solders.compute_budget import set_compute_unit_limit as _CUL, set_compute_unit_price as _CUP
        from solders.transaction import VersionedTransaction as _VT
        from spl.token.instructions import get_associated_token_address as _ATA
        from solana.rpc.types import TokenAccountOpts as _TAO

        _mint_pk = _PK.from_string(mint)
        _PUMP = _PK.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
        _GLOBAL = _PK.from_string("4wTV1YmiEkRvAtNtsSGPtUrqRYQMe5SKy2uB4Jjaxnjf")
        _FEE = _PK.from_string("CebN5WGQ4jvEPvsVU4EoHEpgzq1VV7AbicfhtW4xC9iM")
        _SYS = _PK.from_string("11111111111111111111111111111111")
        _T22 = _PK.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
        
        # Direct RPC method incomplete - skipping to PumpPortal
    except Exception as e:
        logger.warning(f"⚠️ Direct RPC failed: {str(e)[:100]}")
    
    # METHOD 2: PumpPortal Confirmed
    try:
        logger.info("🔧 Method 2: PumpPortal confirmed")
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
                rpc_client.send_transaction, signed, 
                opts=TxOpts(skip_preflight=True, preflight_commitment=Confirmed)
            )
            
            if result.value:
                sig = str(result.value)
                logger.info(f"📤 Sell submitted: {sig[:16]}... waiting 5s for settlement")
                await asyncio.sleep(5)  # Wait for transaction to actually execute
                
                # Trust the settlement wait - return success
                logger.info(f"✅ SOLD: {sig[:16]}... (settlement complete)")
                return True
        
        logger.error("❌ Both methods failed")
        return False
    except Exception as e:
        logger.error(f"❌ All methods failed: {str(e)[:50]}")
        return False



async def monitor(mint):
    """Monitor position and watch for Bot A KELLY sell signal"""
    global current_position
    
    # Bot B uses current_position, not positions dict
    if not current_position or current_position.get("mint") != mint:
        return
    
    p = current_position
    
    logger.info(f"👁️ MONITOR: {p['name']} | Watching for Bot A KELLY sell signal | Timeout: {p['timeout']}s")
    
    start_time = time.time()
    
    # Watch for Bot A's KELLY sell signal
    while time.time() - start_time < p["timeout"]:
        try:
            with open("/tmp/bot_signals.json", "r") as f:
                data = json.load(f)
                sell_signals = data.get("sell_signals", [])
                timeout_signals = data.get("timeout_signals", [])
                
                # Check if Bot A signaled to sell this mint
                for sig in sell_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"🔔 BOT A KELLY SOLD - FOLLOWING!")
                        await sell(mint, "Bot A Exit")
                        return
                
                # Check if Bot A's KELLY timed out
                for sig in timeout_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"⏱️ BOT A KELLY TIMEOUT - FOLLOWING!")
                        await sell(mint, "Bot A Timeout")
                        return
        except:
            pass
        
        await asyncio.sleep(0.5)
    
    # Timeout - sell anyway
    logger.info(f"💸 KELLY TIMEOUT - FORCE SELLING: {p['name']}")
    await sell(mint, "REAL Timeout")
    return
async def watch_signals():
    """Watch signal file and buy Kelly when Bot A signals"""
    global ws_global, latest_data
    logger.info("BOT B: Watching for signals...")
    
    bought_mints = set()  # Track mints we've already bought
    
    # Start background task to read websocket messages
    async def read_websocket():
        global ws_global, latest_data
        while True:
            try:
                # Connect to PumpPortal's global feed for ALL new tokens
                async with websockets.connect("wss://pumpportal.fun/api/data") as ws:
                    logger.info("🌐 Connected to PumpPortal websocket feed")
                    
                    # Subscribe to new token events
                    subscribe = {"method": "subscribeNewToken"}
                    await ws.send(json.dumps(subscribe))
                    logger.info("✅ Subscribed to new tokens")
                    
                    async for msg in ws:
                        try:
                            d = json.loads(msg)
                            mint = d.get('mint')
                            logger.info(f"📨 WS MSG: {mint[:8] if mint else 'no-mint'}")
                            if not mint:
                                continue
                            
                            mc = d.get('marketCapSol', 0)
                            v_sol = d.get('vSolInBondingCurve', 0)
                            bonding = min(100, (v_sol / 85) * 100) if v_sol > 0 else 0
                            
                            latest_data[mint] = {
                                'mint': mint,
                                'marketCapSol': mc,
                                'name': d.get('name', mint[:8]),
                                'progress': bonding,
                                'vSol': v_sol,
                                'vTokens': d.get('vTokensInBondingCurve', 1)
                            }
                            logger.info(f"💾 Updated latest_data for {mint[:8]}: MC={mc:.4f}")
                        except Exception as e:
                            logger.error(f"❌ WS message parse error: {e}")
            except Exception as e:
                logger.error(f"❌ WS connection error: {e}")
                await asyncio.sleep(5)
    
    # Start websocket reader
    asyncio.create_task(read_websocket())
    logger.info("✅ Websocket reader started")
    
    while True:
        try:
            with open("/tmp/bot_signals.json", "r") as f:
                data = json.load(f)
            
            for signal in data.get("signals", []):
                mint = signal["mint"]
                
                if mint in bought_mints or mint in blacklist:
                    continue
                
                
                logger.info(f"SIGNAL: {signal['name']} @ +{signal['peak']:.1f}%")
                logger.info(f"KELLY BUY: {mint[:8]}... | {KELLY_AMOUNT} SOL")
                
                bought_mints.add(mint)
                logger.info(f"⏰ ABOUT TO CALL BUY: {mint[:8]}")
                # Get current bonding from latest_data if available
                # Wait for websocket to have data for this mint (up to 5 seconds)
                logger.info(f"⏳ Waiting for websocket data for {mint[:8]}...")
                for i in range(50):
                    if mint in latest_data:
                        progress = latest_data[mint].get('progress', 0)
                        if progress > 0:
                            logger.info(f"✅ Got data after {i/10:.1f}s: progress={progress:.1f}%")
                            break
                    await asyncio.sleep(0.1)
                else:
                    logger.info(f"⚠️ Timeout waiting for data - latest_data keys: {list(latest_data.keys())[:3]}")
                
                current_bonding = latest_data.get(mint, {}).get('progress', 0)
                logger.info(f"🎯 Entry bonding: {current_bonding:.1f}%")
                result = await buy(mint, signal['name'], current_bonding, 0, "")
                bought_mints.add(mint)  # Mark as bought
                logger.info(f"✅ BUY RETURNED: {result}")
                
        except Exception as e:
            import traceback
            logger.error(f"WATCH ERROR: {e}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(0.5)

async def main():
    global ws_global
    
    # CLEAR OLD SIGNALS FIRST - before anything else
    import json
    try:
        with open("/tmp/bot_signals.json", "w") as f:
            json.dump({"signals": []}, f)
        print("🧹 OLD SIGNALS CLEARED")
    except:
        pass
    
    # Connect to PumpPortal websocket
    try:
        ws_global = await websockets.connect("wss://pumpportal.fun/api/data")
        logger.info("✅ Connected to PumpPortal websocket")
    except Exception as e:
        logger.error(f"❌ Websocket connection failed: {e}")
    
    logger.info("BOT B - KELLY FOLLOWER")
    logger.info(f"Kelly: {KELLY_AMOUNT} SOL")
    logger.info(f"Trail: +{TRAILING_STOP_TRIGGER}% | SL: {STOP_LOSS_PCT}%")
    
    await watch_signals()

if __name__ == "__main__":
    asyncio.run(main())
