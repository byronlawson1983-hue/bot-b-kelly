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
KELLY_AMOUNT = 0.0001
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
            
            timeout=5 if trade_type == "TEST1" else (random.randint(2,3) if trade_type == "TEST2" else random.randint(TIMEOUT_MIN,TIMEOUT_MAX))
            
            # FORCE OVERRIDE for REAL buys - stop TEST monitor immediately
            if trade_type == "REAL":
                await asyncio.sleep(0.1)  # Brief pause to let TEST monitor exit
                logger.info(f"🛑 TEST monitor stopped")
                # CRITICAL: CREATE current_position for REAL/KELLY
                # Check if position already exists (created early in monitor)
                if not current_position:
                    # Recalculate timeout for KELLY/REAL (was calculated for TEST1)
                    kelly_timeout = random.randint(10, 15) if trade_type == "KELLY" else random.randint(TIMEOUT_MIN, TIMEOUT_MAX)
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
    global current_position
    global recycling_queued
    
    if not current_position or current_position["mint"]!=mint:return
    
    p=current_position
    logger.info(f"👁️ MONITOR: {p['name']} | Trail: +{TRAILING_STOP_TRIGGER}% | SL: {STOP_LOSS_PCT}% | Timeout: {p['timeout']}s")
    
    start=time.time()
    last_data_time=time.time()
    
    while current_position and current_position["mint"]==mint and time.time()-start<p["timeout"]:
        # Exit immediately if this position was marked as sold
        if p.get("sell_fired"):
            logger.info(f"🛑 Monitor exiting: {p.get('name')} marked as sold")
            return
        
        d=latest_data.get(mint)
        
        # No data at all after 3s and peak still 0% - dead token, skip fast
        if not d and p.get("peak_pnl",0)<=0 and time.time()-last_data_time>3:
            logger.warning(f"⏭️ NO DATA 3s: {p['name']} - skipping dead token")
            await sell(mint,"NoData")
            return
        
        if d:
            last_data_time=time.time()
            current_bonding=d.get('progress',0)  # Bonding curve %
            entry_bonding=p.get("entry_bonding",0)
            p["last_trade_time"]=time.time()
            
            if current_bonding>0 and entry_bonding>0:
                pnl=((current_bonding-entry_bonding)/entry_bonding)*100
                
                if pnl>p["peak_pnl"]:
                    p["peak_pnl"]=pnl
                
                if pnl>=TRAILING_STOP_TRIGGER and not p["trailing_stop_active"]:
                    if p["trade_type"] in ["TEST1","TEST2"] and not p.get("test_triggered"):
                        p["peak_pnl"]=pnl
                        p["test_triggered"]=True
                        logger.info(f"✅ TEST APPROVED: {p['name']} @ +{pnl:.1f}% - holding position")
                        
                        # Mark as approved but continue trailing to sell
                        if p["trade_type"]=="TEST1":
                            logger.info(f"✅ TEST1 PASSED: {p['name']} @ +{pnl:.1f}% - will sell then trigger TEST2")
                            p["test1_approved"] = True
                        elif p["trade_type"]=="TEST2":
                            logger.info(f"✅ TEST2 PASSED: {p['name']} @ +{pnl:.1f}% - will sell then trigger REAL")
                            p["test2_approved"] = True
                        
                    p["trailing_stop_active"]=True
                    logger.info(f"🔒 TRAILING @ +{pnl:.1f}% (Peak: +{p['peak_pnl']:.1f}%)")
                
                if p["trailing_stop_active"] and pnl<=(p["peak_pnl"]-TRAILING_PULLBACK):
                    logger.info(f"📉 TRAIL EXIT @ +{pnl:.1f}% (Peak: +{p['peak_pnl']:.1f}%)")
                    if p.get("sell_fired"):
                        logger.info(f"🔴 SELL BLOCKED: sell_fired already True for {p.get('name')}")
                        return
                    p["sell_fired"] = True
                    p["exit_pnl"]=pnl
                    
                    # Sell first
                    global should_restart, trades_in_cycle
                    
                    await sell(mint,f"Trail +{p['peak_pnl']:.1f}%")
                    logger.info("🔍 DEBUG: Sell returned, about to return from monitor")
                    
                    # CRITICAL: Clear position BEFORE triggering next buy
                    if current_position and current_position["mint"] == mint:
                        current_position = None
                        logger.info(f"✅ Position cleared, ready for next token")
                    
                    # After selling TEST, trigger next stage
                    if p.get("test1_approved") and p.get("trade_type") == "TEST1":
                        peak = p.get("peak_pnl", 0)
                        if peak >= 25:
                            # KELLY CRITERION: High conviction play
                            logger.info(f"💎 KELLY BUY @ {peak:.1f}% - HIGH CONVICTION")
                            # Signal Bot B
                            try:
                                import json as _j, time as _t
                                with open("/tmp/bot_signals.json", "r+") as _f:
                                    _d = _j.load(_f); _d["signals"].append({"mint":mint,"name":p["name"],"peak":peak,"ts":_t.time()}); _f.seek(0); _j.dump(_d,_f); _f.truncate()
                                logger.info("📡 SIGNAL SENT")
                            except: pass
                            # Extend original TEST1 timeout to allow for recycling loops
                            if p.get("trade_type") == "TEST1":
                                p["timeout"] = 120  # 2 minutes for recycling
                                logger.info(f"⏱️ Extended TEST1 timeout to 120s for recycling")
                            kelly_approved_tokens.add(mint)
                # DISABLED - Bot B only buys from signals                            await buy(mint,p['name'],p['entry_bonding'],p['entry_mc'],p['creator'])
                            # Wait for Kelly to complete before TEST1 exits
                            while current_position and current_position.get("trade_type") == "KELLY":
                                await asyncio.sleep(0.5)  # Wait for Kelly monitor
                            logger.info(f"✅ {p.get('trade_type')} completed - TEST1 can exit")
                            # TOKEN RECYCLING: Test the same token again if still viable
                            # Only recycle if didn't hit stop-loss (peak_pnl must be positive)
                            # Calculate exit/peak ratio - only recycle if still pumping (exit close to peak)
                            exit_pnl = p.get("exit_pnl", 0)
                            peak_pnl = p.get("peak_pnl", 0)
                            exit_ratio = exit_pnl / peak_pnl if peak_pnl > 0 else 0
                            
                            # Only recycle if: profitable AND exit within 15% of peak (still pumping)
                            # No bonding check - tokens don't actually graduate on pump.fun
                            if peak_pnl > 0 and exit_ratio >= 0.85:
                                await asyncio.sleep(8)  # Wait for Kelly/REAL sell to fully settle before recycling
                                recycling_queued = True  # Block new tokens
                                logger.info(f'🔄 RECYCLING: {p["name"]} still pumping - testing again!')
                                await asyncio.sleep(6)  # Wait for previous sell to settle
                                # Recycled TEST1 uses Kelly-sized amount (0.005 SOL) for high conviction
                                recycled_tokens.add(mint)
                # DISABLED - Bot B only buys from signals                                await buy(mint, p["name"], p["entry_bonding"], p["entry_mc"], p["creator"])
                                recycling_queued = False
                            else:
                                logger.info(f'✋ {p["name"]} graduated or topped - moving on')
                        elif peak >= 15:
                            logger.info(f"🚀 TEST1 ROCKET @ {peak:.1f}% - REAL BUY")
                            # Extend original TEST1 timeout to allow for recycling
                            if p.get("trade_type") == "TEST1":
                                p["timeout"] = 120  # 2 minutes for recycling
                                logger.info(f"⏱️ Extended TEST1 timeout to 120s for recycling")
                            test_approved_tokens.add(mint)
                # DISABLED - Bot B only buys from signals                            await buy(mint,p['name'],p['entry_bonding'],p['entry_mc'],p['creator'])
                            # Wait for REAL to complete before TEST1 exits
                            while current_position and current_position.get("trade_type") == "REAL":
                                await asyncio.sleep(0.5)  # Wait for REAL monitor
                            logger.info(f"✅ {p.get('trade_type')} completed - TEST1 can exit")
                            # TOKEN RECYCLING: Test the same token again if still viable
                            # Only recycle if didn't hit stop-loss (peak_pnl must be positive)
                            # Calculate exit/peak ratio - only recycle if still pumping (exit close to peak)
                            exit_pnl = p.get("exit_pnl", 0)
                            peak_pnl = p.get("peak_pnl", 0)
                            exit_ratio = exit_pnl / peak_pnl if peak_pnl > 0 else 0
                            
                            # Only recycle if: profitable AND exit within 15% of peak (still pumping)
                            # No bonding check - tokens don't actually graduate on pump.fun
                            if peak_pnl > 0 and exit_ratio >= 0.85:
                                await asyncio.sleep(8)  # Wait for Kelly/REAL sell to fully settle before recycling
                                recycling_queued = True  # Block new tokens
                                logger.info(f'🔄 RECYCLING: {p["name"]} still pumping - testing again!')
                                await asyncio.sleep(6)  # Wait for previous sell to settle
                                # Recycled TEST1 uses Kelly-sized amount (0.005 SOL) for high conviction
                                recycled_tokens.add(mint)
                # DISABLED - Bot B only buys from signals                                await buy(mint, p["name"], p["entry_bonding"], p["entry_mc"], p["creator"])
                                recycling_queued = False
                            else:
                                logger.info(f'✋ {p["name"]} graduated or topped - moving on')
                        else:
                            logger.info(f"🎯 TEST1 sold - triggering TEST2 buy")
                            test2_approved_tokens.add(mint)
                # DISABLED - Bot B only buys from signals                            await buy(mint,p['name'],p['entry_bonding'],p['entry_mc'],p['creator'])
                    elif p.get("test2_approved") and p.get("trade_type") == "TEST2":
                        logger.info(f"🎯 TEST2 sold - triggering REAL buy")
                        test_approved_tokens.add(mint)
                # DISABLED - Bot B only buys from signals                        await buy(mint,p['name'],p['entry_bonding'],p['entry_mc'],p['creator'])
                    
                    # Only count cycles when moving to NEW tokens, not recycling
                    if p.get("trade_type") in ["REAL", "KELLY"]:
                        # Check if we're about to recycle (bonding < 90%)
                        if p.get("entry_bonding", 100) >= 90:
                            # Token is done, count the cycle
                            trades_in_cycle += 1
                            should_restart = True
                            logger.info(f"📊 Cycle: {trades_in_cycle}/{RESTART_AFTER_TRADES}")
                        else:
                            # Token will be recycled, don't count cycle yet
                            logger.info(f"🔄 Recycling loop active - not counting cycle")
                    
                    return
                
                if p["trade_type"] in ["TEST1","TEST2"] and p["peak_pnl"]==0 and (time.time()-p["buy_time"])>2:
                    logger.info(f"⚡ DEAD TOKEN: {p['name']} - instant exit")
                    token_blacklist.add(mint)
                    save_blacklist()
                    sell_result = await sell(mint,"Dead 0%")
                    # Blacklist this dead token
                    token_blacklist.add(mint)
                    logger.info(f"🚫 BLACKLISTED: {mint[:8]}... (dead token)")
                    if sell_result:
                        if current_position and current_position["mint"] == mint:
                            current_position = None
                    else:
                        logger.error(f"❌ DEAD SELL FAILED: {mint[:8]}")
                    return
                if pnl<=STOP_LOSS_PCT:
                    logger.info(f"🛑 SL: {p['name']} @ {pnl:.1f}%")
                    # Blacklist stop-loss tokens - they're rugs, don't retest
                    token_blacklist.add(mint)
                    save_blacklist()
                    logger.info(f"🚫 BLACKLISTED: {mint[:8]}... (stop-loss token)")
                    sell_result = await sell(mint,f"SL {pnl:.1f}%")
                    if sell_result:
                        if current_position and current_position["mint"] == mint:
                            current_position = None
                    else:
                        logger.error(f"❌ SL SELL FAILED: {mint[:8]}")
                    return
        
        time_since_trade=time.time()-p["last_trade_time"]
        if time_since_trade>=VOLUME_DEATH_SECONDS:
            logger.warning(f"💀 VOLUME DEATH: {p['name']}")
            await sell(mint,"Volume Death")
            return
        
        await asyncio.sleep(0.5)
    
    if current_position and current_position["mint"]==mint:
        # Don't timeout REAL positions - they must sell via trailing stop
        if p.get("trade_type") in ["REAL", "KELLY"]:
            logger.info(f"💸 {p.get('trade_type')} TIMEOUT - FORCE SELLING: {p['name']}")
            try:
                await asyncio.wait_for(sell(mint, "REAL Timeout"), timeout=15.0)
                return  # Exit after successful sell
            except asyncio.TimeoutError:
                logger.error(f"❌ Timeout sell hung - force exiting")
                return  # Exit even if sell hangs
            
        if p.get("sell_fired"): return
        p["sell_fired"] = True
        logger.info(f"⏰ TIMEOUT: {p['name']}")
        # FORCE SELL ALL TOKENS IN WALLET
        import requests as _rq, base58 as _b58, struct as _st
        from solders.transaction import VersionedTransaction as _VT
        from solana.rpc.types import TokenAccountOpts
        from solders.pubkey import Pubkey as _PKT
        accs = rpc_client.get_token_accounts_by_owner(wallet.pubkey(), TokenAccountOpts(program_id=_PKT.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"))).value
        for acc in accs:
            data = acc.account.data
            tmint = _b58.b58encode(data[0:32]).decode()
            tamt = _st.unpack('<Q', data[64:72])[0]
            if tamt > 0 and tmint.endswith("pump"):
                try:
                    tr = _rq.post("https://pumpportal.fun/api/trade-local", json={"publicKey": str(wallet.pubkey()), "action": "sell", "mint": tmint, "amount": "100%", "denominatedInSol": "false", "slippage": 100, "priorityFee": 0.0001, "pool": "pump"}, timeout=10)
                    if tr.status_code == 200:
                        tvtx = _VT.from_bytes(tr.content)
                        tvtx = _VT(tvtx.message, [wallet])
                        tsig = rpc_client.send_raw_transaction(bytes(tvtx), opts=TxOpts(skip_preflight=True)).value
                        logger.info(f"💸 FORCE SOLD: {tmint[:8]} → {tsig}")
                        await asyncio.sleep(0.5)
                except: pass
            # TOKEN RECYCLING after Kelly/REAL timeout
            if p and p.get("trade_type") in ["KELLY", "REAL"] and p.get("entry_bonding", 100) < 90:
                recycling_queued = True  # Block new tokens
                logger.info(f'🔄 RECYCLING: {p["name"]} timed out but still viable!')
                await asyncio.sleep(6)  # Wait for previous sell to settle
                # Recycled TEST1 uses Kelly-sized amount (0.005 SOL) for high conviction
                # DISABLED - Bot B only buys from signals                await buy(mint, p["name"], p.get("entry_bonding"), p.get("entry_mc"), p.get("creator"))
                recycling_queued = False
        else:
            # TEST timeout - check if it passed based on peak
            peak = p.get("peak_pnl", 0)
            if peak >= 10:
                logger.info(f"✅ TEST PASSED: {p['name']} peaked at +{peak:.1f}%")
                # SELL THE PASSED TEST TOKENS FIRST
                await sell(mint, f"Test passed {peak:.1f}%")
                # Then trigger next stage
                # Clear position before triggering next stage
                current_position = None
                # emit() - disabled
                # Pause to ensure position fully clears
                await asyncio.sleep(3)
                if p["trade_type"]=="TEST1":
                    if peak >= 30:
                        logger.info(f"🚀 TEST1 ROCKET @ {peak:.1f}% - REAL BUY")
                        # Extend original TEST1 timeout to allow for recycling
                        if p.get("trade_type") == "TEST1":
                            p["timeout"] = 120  # 2 minutes for recycling
                            logger.info(f"⏱️ Extended TEST1 timeout to 120s for recycling")
                        test_approved_tokens.add(mint)
                # DISABLED - Bot B only buys from signals                        await buy(mint,p['name'],p['entry_bonding'],p['entry_mc'],p['creator'])
                    elif peak >= 25:
                        # Signal Bot B
                        try:
                            import json as _j, time as _t
                            with open("/tmp/bot_signals.json", "r+") as _f:
                                _d = _j.load(_f); _d["signals"].append({"mint":mint,"name":p["name"],"peak":peak,"ts":_t.time()}); _f.seek(0); _j.dump(_d,_f); _f.truncate()
                            logger.info("📡 SIGNAL SENT")
                        except: pass
                        logger.info(f"💎 KELLY BUY @ {peak:.1f}% - HIGH CONVICTION")
                        test_approved_tokens.add(mint)
                # DISABLED - Bot B only buys from signals                        await buy(mint,p['name'],p['entry_bonding'],p['entry_mc'],p['creator'])
                    else:
                        logger.info(f"✅ TEST1 → TEST2")
                        test2_approved_tokens.add(mint)
                # DISABLED - Bot B only buys from signals                        await buy(mint,p['name'],p['entry_bonding'],p['entry_mc'],p['creator'])
                elif p["trade_type"]=="TEST2":
                    logger.info(f"✅ TEST2 → REAL")
                    test_approved_tokens.add(mint)
                # DISABLED - Bot B only buys from signals                    await buy(mint,p['name'],p['entry_bonding'],p['entry_mc'],p['creator'])
            else:
                logger.warning(f"❌ TEST FAILED: {p['name']} only reached +{peak:.1f}%")
                # SELL THE FAILED TEST TOKENS
                await sell(mint, f"Test failed {peak:.1f}%")
            
            # Clear position
            current_position = None
            # emit() - disabled
            return  # Exit monitor after clearing position


# Bot B main logic


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
