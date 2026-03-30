with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Find where timeout is set in the buy function
# Should be near where position is created
old = '''            "timeout":timeout,'''

# Find the line where timeout is calculated and change it to 120
content_lines = content.split('\n')
new_lines = []
for line in content_lines:
    # Change the timeout calculation to 120 seconds
    if 'timeout=' in line and 'TIMEOUT' in line:
        # Replace any timeout calculation with fixed 120
        new_lines.append(line.split('=')[0] + '= 120  # Match Bot A KELLY timeout')
    else:
        new_lines.append(line)

content = '\n'.join(new_lines)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Bot B timeout set to 120 seconds")
