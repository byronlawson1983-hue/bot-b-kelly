with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add global positions to monitor function
old = '''async def monitor(mint):
    """Monitor position and watch for Bot A KELLY sell signal"""
    p=positions.get(mint)'''

new = '''async def monitor(mint):
    """Monitor position and watch for Bot A KELLY sell signal"""
    global positions
    p=positions.get(mint)'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added global positions to monitor")
