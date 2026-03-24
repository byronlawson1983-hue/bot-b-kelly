with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# send_with_retry returns a string, but buy() checks result.value
# Change buy() to handle string return
old = """        if result.value:
            sig=str(result.value)"""

new = """        if result:
            sig = result if isinstance(result, str) else str(result.value)"""

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Fixed result.value check")
