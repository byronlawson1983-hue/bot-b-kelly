with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add missing constants
old = "latest_data = {}  # Track latest price data for monitoring"
new = """latest_data = {}  # Track latest price data for monitoring
VOLUME_DEATH_SECONDS = 2  # Dead token detection"""

content = content.replace(old, new)

# Add subscribe_to_token stub
subscribe_func = '''
def subscribe_to_token(mint):
    """Stub - Bot B doesn't use websocket subscriptions"""
    pass

'''

# Insert before get_balance
content = content.replace('def get_balance()', subscribe_func + 'def get_balance()')

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added VOLUME_DEATH_SECONDS and subscribe_to_token")
