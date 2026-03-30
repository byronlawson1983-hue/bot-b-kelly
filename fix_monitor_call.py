with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add monitor() call back where it was removed
old = '''            # Start monitoring immediately (no settlement wait)
            # REMOVED DUPLICATE MONITOR
            return True'''

new = '''            # Start monitoring immediately (no settlement wait)
            await monitor(mint)
            return True'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added monitor() call back to buy()")
