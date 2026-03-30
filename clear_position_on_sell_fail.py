with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add position clearing when sell fails
old = '''        logger.error("❌ Both methods failed")
        return False
    except Exception as e:
        logger.error(f"❌ All methods failed: {str(e)[:50]}")
        return False'''

new = '''        logger.error("❌ Both methods failed")
        # Clear position even on failure so we don't get stuck
        current_position = None
        return False
    except Exception as e:
        logger.error(f"❌ All methods failed: {str(e)[:50]}")
        # Clear position even on failure so we don't get stuck
        current_position = None
        return False'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Added position clearing on sell failure")
