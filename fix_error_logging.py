with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Replace the generic exception handler with detailed logging
old = '''        except Exception as e:
            logger.warning(f"Watch error: {e}")'''

new = '''        except Exception as e:
            import traceback
            logger.error(f"WATCH ERROR: {e}")
            logger.error(traceback.format_exc())'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added detailed error logging")
