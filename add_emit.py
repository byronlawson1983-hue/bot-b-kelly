with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add emit stub function
emit_func = '''
def emit(event, data):
    """Stub - Bot B doesn't emit events"""
    pass

'''

# Insert before get_balance
content = content.replace('def get_balance()', emit_func + 'def get_balance()')

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added emit stub")
