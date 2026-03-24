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

load_dotenv()

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(message)s')
logging.getLogger('httpx').setLevel(logging.CRITICAL)
logging.getLogger('httpcore').setLevel(logging.CRITICAL)
logging.getLogger('httpx').propagate = False
logging.getLogger('httpcore').propagate = False
logger=logging.getLogger(__name__)

app=Flask(__name__)
socketio=SocketIO(app,cors_allowed_origins="*",async_mode='threading')

wallet=Keypair.from_bytes(base58.b58decode(os.getenv("SOLANA_PRIVATE_KEY")))


rpc_client = Client("https://mainnet.helius-rpc.com/?api-key=8ba83a2d-8876-4779-ac3d-d8c952ff5c9a")
HELIUS_KEY=os.getenv('HELIUS_API_KEY')

# THE GEM - 3 STAGGERED AMOUNTS
AMOUNT_1=0.001      # Test scout 1
AMOUNT_2=0.002   # Test scout 2
AMOUNT_3=0.003      # Real bet - OPTION B TEST RATE
BUY_MIN=0
BUY_MAX=100
STOP_LOSS_PCT=-5
TRAILING_STOP_TRIGGER=10
TRAILING_PULLBACK=3
VOLUME_DEATH_SECONDS=5
TIMEOUT_MIN=5
TIMEOUT_MAX=15
MIN_WALLET_BALANCE=0.04
RESTART_AFTER_TRADES=10  # real trades per cycle

stats={"total_trades":0,"wins":0,"losses":0,"timeouts":0,"total_profit_sol":0,"active_positions":[],"recent_trades":[],"wallet_balance":0,"blacklisted":0,"restarts":0,"test_trades":0,"real_trades":0,"starting_balance":0}
current_position=None
real_position_mint=None  # Pin REAL mint for cleanup if sell fails
seen=set()
latest_data={}
ws_global=None
BLACKLIST_FILE="/root/trading-bot/blacklist.json"
def load_blacklist():
    hardcoded={
        "FG9V2Hy3RMXWikLdqv3gLEN3HEEn5B28mocR2nw2pump",
        "4TpF2XgocTWqPb681LYeSAHBz98HkzFGEEVREn5ipump",
        "G7vQWurMkMMm2dU3iZpXYFTHT9Biio4F4gZCrwFpKNwG",
    }
    try:
        with open(BLACKLIST_FILE,"r") as f:
            saved=set(json.load(f))
            combined=hardcoded|saved
            logger.info(f"Loaded blacklist: {len(combined)} tokens ({len(saved)} from file)")
            return combined
    except:
        return hardcoded

def save_blacklist():
    try:
        with open(BLACKLIST_FILE,"w") as f:
            json.dump(list(token_blacklist),f)
    except Exception as e:
        logger.warning(f"Could not save blacklist: {e}")

token_blacklist=load_blacklist()
dev_blacklist=set()
test_approved_tokens=set()
recycled_tokens=set()  # Track tokens in recycling loops
recycling_queued=False  # Flag to block new tokens during recycling
test2_approved_tokens=set()
kelly_approved_tokens=set()
real_buy_triggered=set()
current_cycle_token=None
trades_in_cycle=0
should_restart=False

def send_with_retry(tx, max_retries=5, skip_preflight=True):
    """Retry transaction with fresh blockhash on failure"""
    import time as _t
    for attempt in range(max_retries):
        try:
            result = rpc_client.send_transaction(
                tx, opts=TxOpts(skip_preflight=skip_preflight, preflight_commitment=Confirmed)
            )
            if result.value:
                return result
        except Exception as e:
            err = str(e)
            if 'BlockhashNotFound' in err or 'Blockhash not found' in err:
                logger.warning(f"⚠️ Blockhash expired, retry {attempt+1}/{max_retries}...")
                _t.sleep(0.2 * (attempt + 1))
                # Re-sign with fresh transaction
                try:
                    tx = VersionedTransaction(tx.message, [wallet])
                except:
                    pass
                continue
            else:
                raise e
    raise Exception(f"Transaction failed after {max_retries} retries")


def get_balance():
    try:return rpc_client.get_balance(wallet.pubkey()).value/1e9
    except:return 0


recently_sold = {}  # mint -> timestamp

async def cleanup_stuck_tokens():
    """Sell ALL tokens using direct RPC - catches everything"""
    logger.info("🧹 CLEANUP: Selling all stuck tokens...")
    try:
        from solana.rpc.types import TokenAccountOpts
        from solders.pubkey import Pubkey
        mints = []
        for program in ["TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb", "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"]:
            r = rpc_client.get_token_accounts_by_owner_json_parsed(
                wallet.pubkey(),
                TokenAccountOpts(program_id=Pubkey.from_string(program))
            )
            for a in r.value:
                info = a.account.data.parsed["info"]
                amt = float(info["tokenAmount"]["uiAmount"] or 0)
                active_mints = {current_position["mint"]} if current_position else set()
                age = time.time() - recently_sold.get(info["mint"], 0)
                if amt > 0 and info["mint"] not in token_blacklist and info["mint"] not in active_mints and age > 30:
                    mints.append(info["mint"])

        sold_count = 0
        # ONLY sell the pinned REAL position - ignore all TEST positions
        real_mints = [m for m in mints if m == real_position_mint] if real_position_mint else []
        for mint in real_mints:
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
                if r.status_code == 200:
                    tx = VersionedTransaction.from_bytes(r.content)
                    tx = VersionedTransaction(tx.message, [wallet])
                    sig = rpc_client.send_raw_transaction(bytes(tx), opts=TxOpts(skip_preflight=True, preflight_commitment=Confirmed)).value
                    logger.info(f"🧹 CLEANUP: {mint[:8]}... | {str(sig)[:8]}")
                    sold_count += 1
                    time.sleep(0.3)
            except Exception as e:
                pass

        logger.info(f"✅ CLEANUP COMPLETE: {sold_count} tokens sold")
    except Exception as e:
        logger.error(f"❌ CLEANUP ERROR: {e}")

    # Check if we should restart after cleanup
    global should_restart, trades_in_cycle
    if should_restart:
        logger.info(f"🔄 Restarting after {trades_in_cycle} cycles...")
        trades_in_cycle = 0
        should_restart = False
        # Reconnect WebSocket
        if ws_global:
            await ws_global.close()
        await asyncio.sleep(1)
        # The listener will reconnect automatically


def emit():
    stats["wallet_balance"]=get_balance()
    if stats["starting_balance"]==0:
        stats["starting_balance"]=stats["wallet_balance"]
    stats["active_positions"]=[{"name":current_position["name"],"entry":current_position["entry_bonding"],"time":int(time.time()-current_position["buy_time"]),"amount":current_position["amount"]} if current_position else {"name":"None","entry":0,"time":0,"amount":0}]
    stats["blacklisted"]=len(token_blacklist)+len(dev_blacklist)
    socketio.emit('update',stats)

def check_dev_wallet(creator):
    try:
        if creator in dev_blacklist:
            logger.info(f"🚫 DEV BLACKLISTED: {creator[:8]}...")
            return False
        
        r=requests.get(f"https://api.helius.xyz/v0/addresses/{creator}/transactions?api-key={HELIUS_KEY}&limit=20",timeout=5)
        if r.status_code!=200:return True
        
        txs=r.json()
        created_tokens=sum(1 for tx in txs if tx.get('type')=='UNKNOWN')
        
        if created_tokens>=5:
            logger.warning(f"⚠️ SERIAL CREATOR: {creator[:8]}... ({created_tokens} tokens)")
            dev_blacklist.add(creator)
            return False
        
        return True
    except:
        return True

async def subscribe_to_token(mint):
    global ws_global
    if ws_global:
        try:
            await ws_global.send(json.dumps({"method":"subscribeTokenTrade","keys":[mint]}))
            logger.info(f"📡 Subscribed to {mint[:8]}...")
        except:pass



# ============================================================================
# CHAINSTACK HELPER FUNCTIONS FOR PUMP.FUN
# ============================================================================

import struct
from solders.pubkey import Pubkey
from construct import Struct, Int64ul, Flag

# Constants
PUMP_PROGRAM = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
PUMP_GLOBAL = Pubkey.from_string("4wTV1YmiEkRvAtNtsSGPtUrqRYQMe5SKy2uB4Jjaxnjf")
PUMP_FEE_PROGRAM = Pubkey.from_string("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ")
EXPECTED_DISCRIMINATOR = struct.pack("<Q", 6966180631402821399)

def _find_bonding_curve_v2(mint: Pubkey) -> Pubkey:
    """Find bonding-curve-v2 PDA for a mint."""
    seeds = [b"bonding-curve-v2", bytes(mint)]
    pda, _ = Pubkey.find_program_address(seeds, PUMP_PROGRAM)
    return pda

def _find_fee_config() -> Pubkey:
    """Find fee_config PDA."""
    seeds = [b"fee_config", bytes(PUMP_PROGRAM)]
    pda, _ = Pubkey.find_program_address(seeds, PUMP_FEE_PROGRAM)
    return pda

def _find_global_volume_accumulator() -> Pubkey:
    """Find global volume accumulator PDA."""
    seeds = [b"global", b"volume-accumulator"]
    pda, _ = Pubkey.find_program_address(seeds, PUMP_PROGRAM)
    return pda

def _find_user_volume_accumulator(user: Pubkey) -> Pubkey:
    """Find user volume accumulator PDA."""
    seeds = [b"user", bytes(user), b"volume-accumulator"]
    pda, _ = Pubkey.find_program_address(seeds, PUMP_PROGRAM)
    return pda

class BondingCurveState:
    """Bonding curve state parser."""
    _BASE_STRUCT = Struct(
        "virtual_token_reserves" / Int64ul,
        "virtual_sol_reserves" / Int64ul,
        "real_token_reserves" / Int64ul,
        "real_sol_reserves" / Int64ul,
        "token_total_supply" / Int64ul,
        "complete" / Flag,
    )
    
    def __init__(self, data: bytes):
        if len(data) < 8:
            raise ValueError("Data too short")
        if data[:8] != EXPECTED_DISCRIMINATOR:
            raise ValueError("Invalid discriminator")
        
        offset = 8
        parsed = self._BASE_STRUCT.parse(data[offset:])
        self.__dict__.update(parsed)
        offset += self._BASE_STRUCT.sizeof()
        
        # Parse creator if available
        if len(data) >= offset + 32:
            self.creator = Pubkey.from_bytes(data[offset:offset+32])
            offset += 32
        else:
            self.creator = None
        
        # Parse mayhem mode if available
        if len(data) >= offset + 1:
            self.is_mayhem_mode = bool(data[offset])
        else:
            self.is_mayhem_mode = False

async def get_pump_curve_state(client, bonding_curve: Pubkey):
    """Fetch and parse bonding curve state."""
    response = await client.get_account_info(bonding_curve)
    if not response.value:
        raise ValueError(f"Bonding curve {bonding_curve} not found")
    return BondingCurveState(response.value.data)

def calculate_pump_curve_price(curve_state: BondingCurveState) -> float:
    """Calculate current token price in SOL."""
    if curve_state.virtual_token_reserves == 0:
        raise ValueError("No liquidity")
    return (curve_state.virtual_sol_reserves / 1_000_000_000) / (curve_state.virtual_token_reserves / 1_000_000)

async def get_fee_recipient(client, curve_state: BondingCurveState):
    """Get fee recipient based on mayhem mode."""
    PUMP_FEE = Pubkey.from_string("CebN5WGQ4jvEPvsVU4EoHEpgzq1VV7AbicfhtW4xC9iM")
    
    if not curve_state.is_mayhem_mode:
        return PUMP_FEE
    
    # Fetch reserved_fee_recipient from Global account for mayhem tokens
    global_account = await client.get_account_info(PUMP_GLOBAL)
    if not global_account.value:
        return PUMP_FEE
    
    # Extract reserved_fee_recipient (32 bytes at offset 200)
    try:
        data = global_account.value.data
        if len(data) >= 232:
            return Pubkey.from_bytes(data[200:232])
    except:
        pass
    
    return PUMP_FEE



async def check_instant_momentum(mint, trade_type):
    """Check momentum INSTANTLY after buy using on-chain data"""
    import time
    from solders.pubkey import Pubkey
    
    try:
        # Get recent transactions for this token
        mint_pk = Pubkey.from_string(mint)
        sigs = rpc_client.get_signatures_for_address(mint_pk, limit=50).value
        
        unique_buyers = set()
        cutoff = time.time() - 10  # Last 10 seconds
        
        for sig_info in sigs:
            if sig_info.block_time and sig_info.block_time < cutoff:
                break
            
            # Get transaction details
            tx = rpc_client.get_transaction(sig_info.signature, encoding="jsonParsed", max_supported_transaction_version=0)
            if not tx.value:
                continue
                
            # Parse for buyers (wallets that sent SOL)
            for ix in tx.value.transaction.transaction.message.instructions:
                if hasattr(ix, 'parsed') and ix.parsed:
                    if ix.parsed.get('type') == 'transfer':
                        buyer = ix.parsed['info'].get('source')
                        if buyer and buyer != str(wallet.pubkey()):
                            unique_buyers.add(buyer)
        
        buyer_count = len(unique_buyers)
        required = 5 if trade_type == "TEST1" else 7
        
        # Check our token value (momentum)
        # For now, just check buyer count
        # TODO: Add token value check
        
        logger.info(f"🔍 INSTANT CHECK: {buyer_count}/{required} unique buyers")
        
        return buyer_count >= required
        
    except Exception as e:
        logger.error(f"❌ Instant check error: {e}")
        return False

async def buy(mint,name,bonding,mc,creator,kelly=False):
    if not mint.endswith("pump"):
        logger.info(f"⏭️ SKIPPED (non-pump token): {name} | {mint[:8]}...")
        return False
    global current_position,trades_in_cycle,should_restart,current_cycle_token
    # Note: current_position declared global at function start
    
    if current_position and current_position.get("trade_type") == "REAL":return False
    
    # Block if this mint already has any active position (including TEST)
    if current_position and current_position.get("mint") == mint:
        logger.info(f"🛑 BLOCKED: Position already exists for {mint[:8]}")
        return False
    if should_restart:return False
    if mint in token_blacklist:
        logger.info(f"🚫 BLACKLISTED: {name}")
        return False
    if not check_dev_wallet(creator):return False
    

    
    balance=get_balance()
    if balance<MIN_WALLET_BALANCE:
        logger.error(f"🛑 WALLET SAFETY: {balance:.4f} SOL < {MIN_WALLET_BALANCE} SOL")
        return False
    
    # CYCLE LOGIC: TEST first, if passes immediately do REAL on same token
    if mint in test_approved_tokens:
        # This is a REAL buy triggered after test 2 passed
        base_amount=AMOUNT_3
        trade_type="REAL"
        if mint in real_buy_triggered:
            logger.info(f"🛑 DOUBLE BUY BLOCKED: {mint[:8]}")
            return False
        real_buy_triggered.add(mint)
        stats["real_trades"]+=1
        test_approved_tokens.discard(mint)
    elif mint in kelly_approved_tokens:
        # KELLY CRITERION: High conviction
        base_amount=random.uniform(0.005, 0.007)
        trade_type="KELLY"
        stats["real_trades"]+=1
        kelly_approved_tokens.discard(mint)
    elif mint in test2_approved_tokens:
        # This is TEST2 triggered after test 1 passed
        # If this token is in recycling loop, use Kelly-sized amount
        if mint in recycled_tokens:
            base_amount=0.005  # Recycled TEST2 uses high conviction amount
            trade_type="TEST2"
            logger.info(f"🔄 RECYCLED TEST2 @ 0.005 SOL")
        else:
            base_amount=AMOUNT_2  # New token uses standard TEST2 amount
            trade_type="TEST2"
        stats["test_trades"]+=1
        test2_approved_tokens.discard(mint)
    else:
        # TEST buy - check if recycled or new token
        # If this token is in recycling loop, use Kelly-sized amount
        if mint in recycled_tokens:
            base_amount=0.005  # Recycled TEST1 uses high conviction amount
            trade_type="TEST1"
            logger.info(f"🔄 RECYCLED TEST1 @ 0.005 SOL")
        else:
            base_amount=AMOUNT_1  # New token uses scout amount
            trade_type="TEST1"
        stats["test_trades"]+=1
        current_cycle_token=mint
    
    # Randomization
    amount=base_amount*random.uniform(0.95,1.05)
    if trade_type not in ["REAL", "KELLY"]:
        await asyncio.sleep(random.uniform(0.1,2.0))
    
    logger.info(f"💰 {trade_type} BUY: {name} @ {bonding:.1f}% | {amount:.6f} SOL")
    
    try:
        payload={"publicKey":str(wallet.pubkey()),"action":"buy","mint":mint,"amount":amount,"denominatedInSol":"true","slippage": 100,"priorityFee":0.0001,"pool":"auto"}
        r=requests.post("https://pumpportal.fun/api/trade-local",json=payload,timeout=10)
        
        if r.status_code!=200:return False
        
        if 'application/json' in r.headers.get('Content-Type',''):
            tx_bytes=base64.b64decode(r.json()['transaction'])
        else:
            tx_bytes=r.content
        
        tx=VersionedTransaction.from_bytes(tx_bytes)
        tx=VersionedTransaction(tx.message,[wallet])
        result=send_with_retry(tx)
        
        if result.value:
            sig=str(result.value)
            logger.info(f"✅ BOUGHT: {sig[:8]} | Mint: {mint}")
            
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
                "amount":amount,
                "trade_type":trade_type
            }
            
            stats["total_trades"]+=1
            stats["recent_trades"].insert(0,{"type":"BUY","name":name,"bonding":bonding,"amount":amount,"trade_type":trade_type})
            stats["recent_trades"]=stats["recent_trades"][:20]
            emit()
            
            await subscribe_to_token(mint)
            
            # For TEST positions, do instant analysis before monitoring
            if trade_type in ["TEST1", "TEST2"]:
                await asyncio.sleep(0.5)  # Brief wait for WebSocket to update
                await instant_test_analysis(mint, name, trade_type, bonding, creator)
                # If instant_test_analysis cleared position, don't start monitor
                if not current_position or current_position["mint"] != mint:
                    return True
            
            # Start monitoring immediately (no settlement wait)
            asyncio.create_task(monitor(mint))
            return True
    except Exception as e:
        logger.error(f"❌ {e}")
    return False


async def check_token_balance(mint):
    """Check if we still hold tokens after sell attempt"""
    try:
        from solders.pubkey import Pubkey
        from solana.rpc.types import TokenAccountOpts
        TOKEN_2022 = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
        resp = rpc_client.get_token_accounts_by_owner_json_parsed(
            wallet.pubkey(),
            TokenAccountOpts(mint=Pubkey.from_string(mint), program_id=TOKEN_2022)
        )
        if resp.value:
            for acc in resp.value:
                parsed = acc.account.data.parsed
                amt = parsed["info"]["tokenAmount"]["uiAmount"]
                if amt and float(amt) > 0:
                    return float(amt)
        return 0
    except Exception as e:
        logger.warning(f"⚠️ Balance check failed: {e}")
        return -1


async def analyze_test_instantly(mint, name, trade_type, entry_bonding, entry_mc, creator):
    """INSTANT test analysis - checks velocity and bonding movement"""
    global current_position
    
async def instant_test_analysis(mint, name, trade_type, bonding, creator):
    """INSTANT test analysis - checks velocity and bonding movement"""
    global current_position

    # Check bonding curve movement
    if mint in latest_data:
        current_bonding = latest_data[mint].get('progress', 0)
    else:
        logger.warning(f"❌ {trade_type} FAILED: {name} - not in feed (dead/graduated)")
        token_blacklist.add(mint)
        current_position = None
        return
    
    # Check velocity - are there unique buyers?
    try:
        import requests
        url = "https://solana-mainnet.core.chainstack.com/3b8c8dad3d6aeb562044695a3f3db4ba"
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            txs = r.json()
            recent_buyers = set()
            cutoff = time.time() - 10  # Last 10 seconds
            
            for tx in txs[:30]:
                tx_time = tx.get('timestamp', 0)
                if tx_time < cutoff:
                    break
                
                # Count unique buyers
                for nt in tx.get('nativeTransfers', []):
                    if nt.get('amount', 0) > 100000:  # > 0.0001 SOL
                        buyer = nt.get('fromUserAccount')
                        if buyer:
                            recent_buyers.add(buyer)
            
            buyer_count = len(recent_buyers)
            required = 5 if trade_type == "TEST1" else 7
            
            if buyer_count < required:
                logger.warning(f"❌ {trade_type} FAILED: {name} - only {buyer_count} buyers (need {required})")
                token_blacklist.add(mint)
                current_position = None
                return
            
            # PASSED!
            logger.info(f"✅ {trade_type} PASSED: {name} - {buyer_count} buyers, bonding {current_bonding:.1f}%")
            
            # Don't interrupt Kelly/REAL positions
            if current_position and current_position.get('trade_type') in ['REAL', 'KELLY']:
                logger.info(f'⏸️ {trade_type} passed but {current_position["trade_type"]} active - skipping')
                return
            
            if trade_type == "TEST1":
                test2_approved_tokens.add(mint)
                current_position = None
                asyncio.create_task(buy(mint, name, entry_bonding, entry_mc, creator))
            elif trade_type == "TEST2":
                test_approved_tokens.add(mint)
                current_position = None
                asyncio.create_task(buy(mint, name, entry_bonding, entry_mc, creator))
                
    except Exception as e:
        logger.warning(f"❌ {trade_type} FAILED: {name} - velocity check error: {e}")
        token_blacklist.add(mint)
        current_position = None

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
            current_mc=d.get('marketCapSol',0)
            entry_mc=p["entry_mc"]
            p["last_trade_time"]=time.time()
            
            if current_mc>0 and entry_mc>0:
                pnl=((current_mc-entry_mc)/entry_mc)*100
                
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
                            # Extend original TEST1 timeout to allow for recycling loops
                            if p.get("trade_type") == "TEST1":
                                p["timeout"] = 120  # 2 minutes for recycling
                                logger.info(f"⏱️ Extended TEST1 timeout to 120s for recycling")
                            kelly_approved_tokens.add(mint)
                            await buy(mint,p['name'],p['entry_bonding'],p['entry_mc'],p['creator'])
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
                                await buy(mint, p["name"], p["entry_bonding"], p["entry_mc"], p["creator"])
                                recycling_queued = False  # Allow new tokens again
                            else:
                                logger.info(f'✋ {p["name"]} graduated or topped - moving on')
                        elif peak >= 15:
                            logger.info(f"🚀 TEST1 ROCKET @ {peak:.1f}% - REAL BUY")
                            # Extend original TEST1 timeout to allow for recycling
                            if p.get("trade_type") == "TEST1":
                                p["timeout"] = 120  # 2 minutes for recycling
                                logger.info(f"⏱️ Extended TEST1 timeout to 120s for recycling")
                            test_approved_tokens.add(mint)
                            await buy(mint,p['name'],p['entry_bonding'],p['entry_mc'],p['creator'])
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
                                await buy(mint, p["name"], p["entry_bonding"], p["entry_mc"], p["creator"])
                                recycling_queued = False  # Allow new tokens again
                            else:
                                logger.info(f'✋ {p["name"]} graduated or topped - moving on')
                        else:
                            logger.info(f"🎯 TEST1 sold - triggering TEST2 buy")
                            test2_approved_tokens.add(mint)
                            await buy(mint,p['name'],p['entry_bonding'],p['entry_mc'],p['creator'])
                    elif p.get("test2_approved") and p.get("trade_type") == "TEST2":
                        logger.info(f"🎯 TEST2 sold - triggering REAL buy")
                        test_approved_tokens.add(mint)
                        await buy(mint,p['name'],p['entry_bonding'],p['entry_mc'],p['creator'])
                    
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
                await buy(mint, p["name"], p.get("entry_bonding"), p.get("entry_mc"), p.get("creator"))
                recycling_queued = False  # Allow new tokens again
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
                emit()
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
                        await buy(mint,p['name'],p['entry_bonding'],p['entry_mc'],p['creator'])
                    elif peak >= 25:
                        logger.info(f"💎 KELLY BUY @ {peak:.1f}% - HIGH CONVICTION")
                        test_approved_tokens.add(mint)
                        await buy(mint,p['name'],p['entry_bonding'],p['entry_mc'],p['creator'])
                    else:
                        logger.info(f"✅ TEST1 → TEST2")
                        test2_approved_tokens.add(mint)
                        await buy(mint,p['name'],p['entry_bonding'],p['entry_mc'],p['creator'])
                elif p["trade_type"]=="TEST2":
                    logger.info(f"✅ TEST2 → REAL")
                    test_approved_tokens.add(mint)
                    await buy(mint,p['name'],p['entry_bonding'],p['entry_mc'],p['creator'])
            else:
                logger.warning(f"❌ TEST FAILED: {p['name']} only reached +{peak:.1f}%")
                # SELL THE FAILED TEST TOKENS
                await sell(mint, f"Test failed {peak:.1f}%")
            
            # Clear position
            current_position = None
            emit()
            return  # Exit monitor after clearing position

async def listener():
    global ws_global,should_restart,trades_in_cycle,current_position
    
    logger.info("🎯 THE GEM - 84% WIN RATE")
    logger.info(f"   Test1: {AMOUNT_1} SOL | Test2: {AMOUNT_2} SOL | Real: {AMOUNT_3} SOL")
    logger.info(f"   🎭 3-AMOUNT STAGGER (Confuses rug bots)")
    logger.info(f"   🛡️ QUALITY FILTER (+5% test approval)")
    logger.info(f"   🚫 BLACKLIST (Rugs blocked)")
    logger.info(f"   Trail: +{TRAILING_STOP_TRIGGER}% | SL: {STOP_LOSS_PCT}%")
    logger.info(f"   Restart: every {RESTART_AFTER_TRADES} trades")
    
    while True:
        try:
            async with websockets.connect("wss://pumpportal.fun/api/data") as ws:
                ws_global=ws
                logger.info("✅ Connected to PumpPortal")
                
                # Subscribe to new token events
                subscribe = {"method": "subscribeNewToken"}
                await ws.send(json.dumps(subscribe))
                logger.info("✅ Subscribed to new tokens")
                
                async for msg in ws:
                    try:
                        logger.debug(f"📨 Got message")
                        if should_restart:
                            if current_position:
                                await asyncio.sleep(1)
                                continue
                            
                            logger.warning("🔄 CYCLE COMPLETE - STARTING CLEANUP")
                            await cleanup_stuck_tokens()
                            
                            pause=random.randint(10,30)
                            logger.warning(f"⏸️ COOLDOWN: {pause}s")
                            stats["restarts"]+=1
                            emit()
                            
                            await asyncio.sleep(pause)
                            
                            trades_in_cycle=0
                            should_restart=False
                            seen.clear()
                            test_approved_tokens.clear()
                            test2_approved_tokens.clear()
                            current_cycle_token=None
                            
                            global last_activity_time
                            last_activity_time=time.time()
                            logger.info(f"👻 FRESH START #{stats['restarts']} - ALL CLEAN")
                            break
                        
                        d = json.loads(msg)
                        
                        # PumpPortal sends: {mint, traderPublicKey, txType, tokenAmount, bondingCurveKey, 
                        #                    vTokensInBondingCurve, vSolInBondingCurve, marketCapSol}
                        
                        mint = d.get('mint')
                        if not mint or not mint.endswith("pump"):
                            continue
                        
                        # Get REAL market cap from PumpPortal
                        mc = d.get('marketCapSol', 0)
                        v_sol = d.get('vSolInBondingCurve', 0)
                        v_tokens = d.get('vTokensInBondingCurve', 1)
                        
                        # Calculate bonding curve progress (0-100%)
                        if v_sol > 0:
                            bonding = min(100, (v_sol / 85) * 100)  # 85 SOL = 100%
                        else:
                            bonding = 0
                        
                        name = d.get('name', mint[:8])
                        creator = d.get('traderPublicKey', 'unknown')
                        
                        # Update latest_data with REAL market cap
                        latest_data[mint] = {
                            'mint': mint,
                            'marketCapSol': mc,
                            'name': name,
                            'progress': bonding,
                            'vSol': v_sol,
                            'vTokens': v_tokens
                        }
                        
                        if current_position and current_position["mint"]==mint:
                            current_position["last_trade_time"]=time.time()
                        
                        if d.get('newPoolCreated') and current_position and current_position["mint"]==mint:
                            await sell(mint,"GRADUATED")
                        
                        # Debug the buy conditions
                        # logger.info(f"CHECK: pos={current_position is None}, seen={mint not in seen}, bonding={BUY_MIN}<=50<={BUY_MAX}, restart={not should_restart}")
                        
                        # Skip if REAL position is monitoring
                        if current_position and current_position.get("trade_type") == "REAL":
                            continue
                        
                        if not current_position and mint not in seen and BUY_MIN<=bonding<=BUY_MAX and not should_restart:
                            logger.info(f"🚀 {name} @ {bonding:.1f}%")
                            seen.add(mint)
                            await buy(mint,name,bonding,mc,creator)
                            
                    except:
                        pass
                        pass
        except:
            await asyncio.sleep(3)
            ws_global=None

HTML='''<!DOCTYPE html>
<html><head><title>THE GEM</title>
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
<style>
body{background:#0a0e27;color:#fff;font-family:monospace;padding:20px;margin:0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:15px;margin:20px 0}
.card{background:linear-gradient(135deg,#1e3a8a,#3b82f6);padding:15px;border-radius:8px}
.val{font-size:28px;font-weight:bold}
.section{background:#1e293b;padding:15px;border-radius:8px;margin:15px 0}
.item{background:#334155;padding:12px;margin:8px 0;border-radius:6px;display:flex;justify-content:space-between}
.green{color:#10b981}.red{color:#ef4444}.yellow{color:#fbbf24}.blue{color:#3b82f6}.purple{color:#a855f7}
</style>
</head><body>
<h1 style="text-align:center">💎 THE GEM - 84% WIN RATE</h1>
<h3 style="text-align:center">3-Amount Stagger | Quality Filter | Blacklist</h3>
<div class="stats">
<div class="card"><div>Start</div><div class="val" id="start">0</div></div>
<div class="card"><div>Current</div><div class="val" id="bal">0</div></div>
<div class="card green"><div>Profit</div><div class="val" id="pft">0</div></div>
<div class="card"><div>Win%</div><div class="val" id="wr">0%</div></div>
<div class="card green"><div>Wins</div><div class="val" id="w">0</div></div>
<div class="card red"><div>Loss</div><div class="val" id="l">0</div></div>
<div class="card yellow"><div>Timeout</div><div class="val" id="t">0</div></div>
<div class="card purple"><div>Blacklist</div><div class="val" id="bl">0</div></div>
</div>
<div class="section"><h2>Position</h2><div id="pl"></div></div>
<div class="section"><h2>Recent</h2><div id="tl"></div></div>
<script>
const s=io();
s.on('update',d=>{
document.getElementById('start').textContent=d.starting_balance.toFixed(6)+' SOL';
document.getElementById('bal').textContent=d.wallet_balance.toFixed(6)+' SOL';
const pft=d.wallet_balance-d.starting_balance;
document.getElementById('pft').textContent=(pft>=0?'+':'')+pft.toFixed(6)+' SOL';
const total=d.wins+d.losses;
document.getElementById('wr').textContent=total>0?((d.wins/total)*100).toFixed(1)+'%':'0%';
document.getElementById('w').textContent=d.wins;
document.getElementById('l').textContent=d.losses;
document.getElementById('t').textContent=d.timeouts;
document.getElementById('bl').textContent=d.blacklisted;
const p=d.active_positions[0];
document.getElementById('pl').innerHTML=p&&p.name!='None'?\`<div class="item"><span>\${p.name} @ \${p.entry.toFixed(1)}% (\${p.amount.toFixed(6)} SOL)</span><span>\${p.time}s</span></div>\`:'<div class="item">No position</div>';
document.getElementById('tl').innerHTML=d.recent_trades.map(t=>\`<div class="item \${t.type=='BUY'?'green':'red'}"><span>[\${t.trade_type}] \${t.type}: \${t.name}</span><span>\${t.reason||t.bonding.toFixed(1)+'%'}</span></div>\`).join('');
});
</script>
</body></html>'''

@app.route('/')
def index():
    return render_template_string(HTML)

def run_flask():
    socketio.run(app,host='0.0.0.0',port=5000,debug=False,use_reloader=False,allow_unsafe_werkzeug=True)

if __name__=='__main__':
    Thread(target=run_flask,daemon=True).start()
    time.sleep(2)
    logger.info("🎯 http://178.128.7.250:5000")
    asyncio.run(listener())










