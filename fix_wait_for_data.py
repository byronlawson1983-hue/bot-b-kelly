with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add wait for websocket data before buying
old = '''                current_bonding = latest_data.get(mint, {}).get('progress', 0)
                result = await buy(mint, signal['name'], current_bonding, 0, "")'''

new = '''                # Wait for websocket to have data for this mint (up to 5 seconds)
                for i in range(50):
                    if mint in latest_data and latest_data[mint].get('progress', 0) > 0:
                        break
                    await asyncio.sleep(0.1)
                
                current_bonding = latest_data.get(mint, {}).get('progress', 0)
                logger.info(f"🎯 Entry bonding: {current_bonding:.1f}%")
                result = await buy(mint, signal['name'], current_bonding, 0, "")'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added wait for websocket data before buying")
