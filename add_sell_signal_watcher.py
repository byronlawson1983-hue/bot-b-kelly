with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Replace the monitor with immediate sell on signal
old = '''    async def monitor(mint):
        """Monitor position and sell on trail or timeout"""
        p=positions.get(mint)
        if not p:
            return
        
        logger.info(f"👁️ MONITOR: {p['name']} | Trail: +{TRAILING_STOP_TRIGGER}% | SL: {STOP_LOSS_PCT}% | Timeout: {p['timeout']}s")'''

new = '''    async def monitor(mint):
        """Monitor position and watch for Bot A KELLY sell signal"""
        p=positions.get(mint)
        if not p:
            return
        
        logger.info(f"👁️ MONITOR: {p['name']} | Watching for Bot A KELLY sell signal | Timeout: {p['timeout']}s")
        
        start_time = time.time()
        
        # Watch for Bot A's KELLY sell signal
        while time.time() - start_time < p["timeout"]:
            try:
                with open("/tmp/bot_signals.json", "r") as f:
                    data = json.load(f)
                    sell_signals = data.get("sell_signals", [])
                    
                    # Check if Bot A signaled to sell this mint
                    for sig in sell_signals:
                        if sig.get("mint") == mint:
                            logger.info(f"🔔 BOT A KELLY SOLD - FOLLOWING!")
                            await sell(mint, "Bot A Exit")
                            return
            except:
                pass
            
            await asyncio.sleep(0.5)
        
        # Timeout - sell anyway
        logger.info(f"💸 KELLY TIMEOUT - FORCE SELLING: {p['name']}")
        await sell(mint, "REAL Timeout")
        return'''

# Find the rest of the old monitor function and remove it
# We need to keep the function signature but replace the body
lines = content.split('\n')
new_lines = []
in_monitor = False
monitor_indent = 0
skip_until_next_function = False

for i, line in enumerate(lines):
    if 'async def monitor(mint):' in line:
        in_monitor = True
        monitor_indent = len(line) - len(line.lstrip())
        # Add the new monitor function
        new_lines.append(new)
        skip_until_next_function = True
        continue
    
    if skip_until_next_function:
        # Skip until we find the next function or end of monitor
        if line.strip() and not line.strip().startswith('#'):
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= monitor_indent and (line.strip().startswith('async def') or line.strip().startswith('def')):
                skip_until_next_function = False
                new_lines.append(line)
        continue
    
    new_lines.append(line)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write('\n'.join(new_lines))

print("✅ Bot B will now follow Bot A's KELLY sell signals")
