with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add async task to process websocket messages
message_handler = '''
async def process_websocket_messages():
    """Background task to process websocket messages and update latest_data"""
    global ws_global, latest_data
    
    while True:
        try:
            if ws_global:
                async for msg in ws_global:
                    try:
                        d = json.loads(msg)
                        mint = d.get('mint')
                        if not mint:
                            continue
                        
                        # Update latest_data with price info
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
                    except:
                        pass
            else:
                await asyncio.sleep(1)
        except:
            await asyncio.sleep(3)

'''

# Insert before watch_signals
content = content.replace('async def watch_signals', message_handler + 'async def watch_signals')

# Start the background task in main()
old = '''    # Connect to PumpPortal websocket
    try:
        ws_global = await websockets.connect("wss://pumpportal.fun/api/data")
        logger.info("✅ Connected to PumpPortal websocket")
    except Exception as e:
        logger.error(f"❌ Websocket connection failed: {e}")'''

new = '''    # Connect to PumpPortal websocket
    try:
        ws_global = await websockets.connect("wss://pumpportal.fun/api/data")
        logger.info("✅ Connected to PumpPortal websocket")
        
        # Start background task to process messages
        asyncio.create_task(process_websocket_messages())
        logger.info("✅ Websocket message handler started")
    except Exception as e:
        logger.error(f"❌ Websocket connection failed: {e}")'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added websocket message handler")
