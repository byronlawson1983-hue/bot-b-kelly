with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add websocket connection at the start of main()
old = '''async def main():
    # CLEAR OLD SIGNALS FIRST - before anything else
    import json
    try:
        with open("/tmp/bot_signals.json", "w") as f:
            json.dump({"signals": []}, f)
        print("🧹 OLD SIGNALS CLEARED")
    except:
        pass
    
    logger.info("BOT B - KELLY FOLLOWER")'''

new = '''async def main():
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
    
    logger.info("BOT B - KELLY FOLLOWER")'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added websocket connection at startup")
