with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Remove the await from instant_test_analysis call
content = content.replace(
    'await instant_test_analysis(mint, name, trade_type, bonding, creator)',
    'instant_test_analysis(mint, name, trade_type, bonding, creator)'
)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Removed await from instant_test_analysis")
