with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add signal file clearing at the start of main()
old = '''async def main():
    logger.info("🤖 BOT B - KELLY FOLLOWER")'''

new = '''async def main():
    # Clear old signals on startup
    import json
    try:
        with open("/tmp/bot_signals.json", "w") as f:
            json.dump({"signals": []}, f)
        logger.info("🧹 Cleared old signals")
    except:
        pass
    
    logger.info("🤖 BOT B - KELLY FOLLOWER")'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Bot B will clear signals on startup")
