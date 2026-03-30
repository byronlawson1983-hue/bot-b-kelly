with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Change from 30 to 15
old = 'kelly_timeout = 30  # Quick exit if Bot A doesn\'t signal'
new = 'kelly_timeout = 15  # Quick exit - most signals come in 13-15s'

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Bot B timeout set to 15 seconds")
