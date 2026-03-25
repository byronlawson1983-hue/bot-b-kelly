with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add a set to track already-bought mints
old = '''async def watch_signals():
    """Watch signal file and buy Kelly when Bot A signals"""
    global ws_global, latest_data
    logger.info("BOT B: Watching for signals...")'''

new = '''async def watch_signals():
    """Watch signal file and buy Kelly when Bot A signals"""
    global ws_global, latest_data
    logger.info("BOT B: Watching for signals...")
    
    bought_mints = set()  # Track mints we've already bought'''

content = content.replace(old, new)

# Skip if already bought this mint
old2 = '''            for signal in signals:
                mint = signal.get("mint")
                
                # Wait for websocket to have data for this mint (up to 5 seconds)'''

new2 = '''            for signal in signals:
                mint = signal.get("mint")
                
                # Skip if we already bought this mint
                if mint in bought_mints:
                    continue
                
                # Wait for websocket to have data for this mint (up to 5 seconds)'''

content = content.replace(old2, new2)

# Add to bought_mints after buying
old3 = '''                current_bonding = latest_data.get(mint, {}).get('progress', 0)
                logger.info(f"🎯 Entry bonding: {current_bonding:.1f}%")
                result = await buy(mint, signal['name'], current_bonding, 0, "")
                logger.info(f"✅ BUY RETURNED: {result}")'''

new3 = '''                current_bonding = latest_data.get(mint, {}).get('progress', 0)
                logger.info(f"🎯 Entry bonding: {current_bonding:.1f}%")
                result = await buy(mint, signal['name'], current_bonding, 0, "")
                bought_mints.add(mint)  # Mark as bought
                logger.info(f"✅ BUY RETURNED: {result}")'''

content = content.replace(old3, new3)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Bot B will now ignore duplicate signals for same mint")
