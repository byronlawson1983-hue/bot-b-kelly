with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Fix the broken try/except block
old = '''    # Connect to PumpPortal websocket
    try:
        ws_global = await websockets.connect("wss://pumpportal.fun/api/data")
        logger.info("✅ Connected to PumpPortal websocket")
        
        # Start background task to process messages
        except Exception as e:
        logger.error(f"❌ Websocket connection failed: {e}")'''

new = '''    # Connect to PumpPortal websocket
    try:
        ws_global = await websockets.connect("wss://pumpportal.fun/api/data")
        logger.info("✅ Connected to PumpPortal websocket")
    except Exception as e:
        logger.error(f"❌ Websocket connection failed: {e}")'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Fixed syntax error")
