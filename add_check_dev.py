with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add a simple check_dev_wallet function before buy()
check_dev_func = '''
def check_dev_wallet(creator):
    """Stub function - Bot B doesn't need dev wallet checking"""
    return False

'''

# Find where buy() starts and insert before it
content = content.replace('async def buy(', check_dev_func + 'async def buy(')

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added check_dev_wallet")
