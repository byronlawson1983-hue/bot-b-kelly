with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Remove the incorrectly placed TEST2 block (after except)
bad_block = '''        except:
                
                # Check if Bot A's TEST2 sold (trail exit)
                test2_sell_signals = data.get("test2_sell_signals", [])
                for sig in test2_sell_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"📡 BOT A TEST2 SOLD - FOLLOWING!")
                        await sell(mint, "Test2 Exit")
                        return
            pass'''

good_block = '''        except:
            pass'''

content = content.replace(bad_block, good_block)

# Now add TEST2 block in the right place (inside try, after TEST1 sell signals)
old = '''                test1_sell_signals = data.get("test1_sell_signals", [])
                for sig in test1_sell_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"📡 BOT A TEST1 SOLD - FOLLOWING!")
                        await sell(mint, "Test1 Exit")
                        return
        except:'''

new = '''                test1_sell_signals = data.get("test1_sell_signals", [])
                for sig in test1_sell_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"📡 BOT A TEST1 SOLD - FOLLOWING!")
                        await sell(mint, "Test1 Exit")
                        return
                
                # Check if Bot A's TEST2 sold (trail exit)
                test2_sell_signals = data.get("test2_sell_signals", [])
                for sig in test2_sell_signals:
                    if sig.get("mint") == mint:
                        logger.info(f"📡 BOT A TEST2 SOLD - FOLLOWING!")
                        await sell(mint, "Test2 Exit")
                        return
        except:'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ TEST2 signal fixed with correct indentation")
