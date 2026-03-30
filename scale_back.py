with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Scale back to 0.013 SOL
old = 'KELLY_AMOUNT = 0.035'
new = 'KELLY_AMOUNT = 0.013'

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Bot B scaled back to 0.013 SOL")
