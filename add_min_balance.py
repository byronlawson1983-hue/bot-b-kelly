with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add MIN_WALLET_BALANCE with other constants
old = "KELLY_AMOUNT = 0.005"
new = """MIN_WALLET_BALANCE = 0.01  # Minimum SOL to keep in wallet
KELLY_AMOUNT = 0.005"""

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added MIN_WALLET_BALANCE")
