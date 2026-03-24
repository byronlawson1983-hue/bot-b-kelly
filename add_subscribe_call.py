with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add subscribe_to_token call after BOUGHT
old = """            logger.info(f"✅ BOUGHT: {sig[:8]} | Mint: {mint}")
            
            # Monitor this position
            asyncio.create_task(monitor(mint))"""

new = """            logger.info(f"✅ BOUGHT: {sig[:8]} | Mint: {mint}")
            
            # Subscribe to websocket for price data
            await subscribe_to_token(mint)
            
            # Monitor this position
            asyncio.create_task(monitor(mint))"""

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added subscribe_to_token call after buy")
