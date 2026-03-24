with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Find where buy creates current_position and add monitor call
old = '''            logger.info(f"✅ BOUGHT: {sig[:8]} | Mint: {mint}")
            
            timeout=5 if trade_type == "TEST1"'''

new = '''            logger.info(f"✅ BOUGHT: {sig[:8]} | Mint: {mint}")
            
            # Monitor this position
            asyncio.create_task(monitor(mint))
            
            timeout=5 if trade_type == "TEST1"'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added monitor() call after buy")
