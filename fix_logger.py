with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Add logger import and setup after the imports section
logger_setup = '''
import logging
import sys

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
'''

# Insert after imports, before the first constant
lines = content.split('\n')
new_lines = []
imports_done = False

for i, line in enumerate(lines):
    new_lines.append(line)
    
    # After load_dotenv(), add logger setup
    if 'load_dotenv()' in line and not imports_done:
        new_lines.append(logger_setup)
        imports_done = True

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write('\n'.join(new_lines))

print("✅ Logger added to Bot B")
