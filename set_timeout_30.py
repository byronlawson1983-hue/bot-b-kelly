with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Change kelly_timeout from 120 to 30
old = 'kelly_timeout = 120  # Match Bot A KELLY timeout'
new = 'kelly_timeout = 30  # Quick exit if Bot A doesn\'t signal'

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Bot B timeout changed to 30 seconds")
