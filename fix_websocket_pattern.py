with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Remove the broken process_websocket_messages function
import re
content = re.sub(r'async def process_websocket_messages\(\):.*?(?=\nasync def )', '', content, flags=re.DOTALL)

# Remove the create_task call
content = content.replace('asyncio.create_task(process_websocket_messages())\n        logger.info("✅ Websocket message handler started")\n    ', '')

# Modify watch_signals to process websocket messages inline
old_watch = '''async def watch_signals():
    """Watch signal file and buy Kelly when Bot A signals"""
    logger.info("BOT B: Watching for signals...")
    
    while True:'''

new_watch = '''async def watch_signals():
    """Watch signal file and buy Kelly when Bot A signals"""
    global ws_global, latest_data
    logger.info("BOT B: Watching for signals...")
    
    # Start background task to read websocket messages
    async def read_websocket():
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
                await asyncio.sleep(1)
    
    # Start websocket reader
    asyncio.create_task(read_websocket())
    logger.info("✅ Websocket reader started")
    
    while True:'''

content = content.replace(old_watch, new_watch)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Fixed websocket message processing")
