with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add clear at the START of main(), before any logs
old = '''async def main():
    logger.info("BOT B - KELLY FOLLOWER")'''

new = '''async def main():
    # CLEAR OLD SIGNALS FIRST - before anything else
    import json
    try:
        with open("/tmp/bot_signals.json", "w") as f:
            json.dump({"signals": []}, f)
        print("🧹 OLD SIGNALS CLEARED")
    except:
        pass
    
    logger.info("BOT B - KELLY FOLLOWER")'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Signal clear added to main() properly")
