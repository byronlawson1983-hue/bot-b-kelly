with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add logging right before and after buy call
old = '''                bought_mints.add(mint)
                await buy(mint, signal['name'], 0, 0, "")'''

new = '''                bought_mints.add(mint)
                logger.info(f"⏰ ABOUT TO CALL BUY: {mint[:8]}")
                result = await buy(mint, signal['name'], 0, 0, "")
                logger.info(f"✅ BUY RETURNED: {result}")'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added buy() debug logging")
