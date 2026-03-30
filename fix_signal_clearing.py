with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Find and replace the signal clearing
old = '''        with open("/tmp/bot_signals.json", "w") as f:
            json.dump({"signals": []}, f)'''

new = '''        with open("/tmp/bot_signals.json", "w") as f:
            json.dump({
                "signals": [],
                "test1_sell_signals": [],
                "test2_sell_signals": [],
                "kelly_buy_signals": [],
                "real_buy_signals": [],
                "test2_fail_signals": [],
                "kelly_timeout_signals": []
            }, f)'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Bot B now clears ALL signal types on startup")
