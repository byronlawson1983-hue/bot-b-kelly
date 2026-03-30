with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Find and replace KELLY_AMOUNT
old = 'KELLY_AMOUNT = 0.013'
new = 'KELLY_AMOUNT = 0.035'

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Bot B position size updated to 0.035 SOL")
