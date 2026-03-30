with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Replace positions.get(mint) with current_position
old = '''async def monitor(mint):
    """Monitor position and watch for Bot A KELLY sell signal"""
    global positions
    p=positions.get(mint)
    if not p:
        return'''

new = '''async def monitor(mint):
    """Monitor position and watch for Bot A KELLY sell signal"""
    global current_position
    
    # Bot B uses current_position, not positions dict
    if not current_position or current_position.get("mint") != mint:
        return
    
    p = current_position'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Monitor now uses current_position instead of positions")
