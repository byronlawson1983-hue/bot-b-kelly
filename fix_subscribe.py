with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Make subscribe_to_token async so it can be awaited
old = '''def subscribe_to_token(mint):
    """Stub - Bot B doesn't use websocket subscriptions"""
    pass'''

new = '''async def subscribe_to_token(mint):
    """Stub - Bot B doesn't use websocket subscriptions"""
    pass'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Made subscribe_to_token async")
