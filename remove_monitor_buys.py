with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Find the monitor function and remove all buy() calls from it
import re

# This is complex - let me just comment out all buy calls in monitor
# Lines 430-628 are in the monitor function
lines = content.split('\n')
new_lines = []

in_monitor = False
for i, line in enumerate(lines, 1):
    if 'async def monitor(' in line:
        in_monitor = True
    elif in_monitor and 'async def ' in line and 'monitor' not in line:
        in_monitor = False
    
    # If in monitor and line has 'await buy(', comment it out
    if in_monitor and 'await buy(' in line:
        new_lines.append('                # DISABLED - Bot B only buys from signals' + line)
    else:
        new_lines.append(line)

content = '\n'.join(new_lines)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Removed all buy() calls from monitor")
