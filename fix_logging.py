with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Change debug to info so we can see the messages
content = content.replace(
    'logger.debug(f"📨 WS MSG: {mint[:8] if mint else \'no-mint\'}")',
    'logger.info(f"📨 WS MSG: {mint[:8] if mint else \'no-mint\'}")'
)

content = content.replace(
    'logger.debug(f"💾 Updated latest_data for {mint[:8]}: MC={mc:.4f}")',
    'logger.info(f"💾 Updated latest_data for {mint[:8]}: MC={mc:.4f}")'
)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Changed debug logs to info logs")
