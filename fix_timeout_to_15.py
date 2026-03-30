with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Change the timeout=120 line to timeout=15
old = '''            timeout= 120  # Match Bot A KELLY timeout'''
new = '''            timeout= 15  # Bot B doesn't need 120s - no TEST positions'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Changed timeout from 120 to 15 at line 174")
