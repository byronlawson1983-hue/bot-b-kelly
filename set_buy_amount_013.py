with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Change base_amount from 0.01 to 0.013
old = 'base_amount = 0.01  # Bot B uses 0.01 SOL Kelly positions'
new = 'base_amount = 0.013  # Bot B uses 0.013 SOL Kelly positions'

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Bot B buy amount increased to 0.013 SOL")
