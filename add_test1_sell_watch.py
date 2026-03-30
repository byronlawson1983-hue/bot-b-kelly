with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add TEST1 sell signal to the monitor function
old_monitor = '''                # Check if Bot A's TEST2 failed (abort!)
                for sig in test2_fail_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"⚠️ BOT A TEST2 FAILED - ABORTING!")
                        await sell(mint, "Test2 Abort")
                        return'''

new_monitor = '''                # Check if Bot A's TEST2 failed (abort!)
                for sig in test2_fail_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"⚠️ BOT A TEST2 FAILED - ABORTING!")
                        await sell(mint, "Test2 Abort")
                        return
                
                # Check if Bot A's TEST1 sold (trail exit)
                test1_sell_signals = data.get("test1_sell_signals", [])
                for sig in test1_sell_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"📡 BOT A TEST1 SOLD - FOLLOWING!")
                        await sell(mint, "Test1 Exit")
                        return'''

content = content.replace(old_monitor, new_monitor)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Bot B now watches TEST1 sell signals")
