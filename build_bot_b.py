# Build Bot B by combining skeleton + extracted functions

# Read extracted functions
with open("/tmp/bot_functions.txt", "r") as f:
    functions = f.read()

# Parse sections
sections = {}
current_section = None
current_content = []

for line in functions.split('\n'):
    if line.startswith('=== '):
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        current_section = line.strip('= \n')
        current_content = []
    else:
        current_content.append(line)

if current_section:
    sections[current_section] = '\n'.join(current_content)

# Build complete Bot B
bot_b = f'''#!/usr/bin/env python3
"""
BOT B - Kelly-Only Follower
Watches Bot A signals and buys Kelly with separate wallet
"""
{sections.get('IMPORTS', '')}
from dotenv import load_dotenv

load_dotenv()

# Constants
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RPC_ENDPOINT = os.getenv("RPC_ENDPOINT", "https://api.mainnet-beta.solana.com")

{sections.get('CONSTANTS', '')}

# Bot B specific settings
KELLY_AMOUNT = 0.005
bought_mints = set()
current_position = None
blacklist = set()

# Functions from Bot A
{sections.get('BUY', '')}

{sections.get('SELL', '')}

{sections.get('MONITOR', '')}

# Bot B main logic
async def watch_signals():
    """Watch signal file and buy Kelly when Bot A signals"""
    logger.info("BOT B: Watching for signals...")
    
    while True:
        try:
            with open("/tmp/bot_signals.json", "r") as f:
                data = json.load(f)
            
            for signal in data.get("signals", []):
                mint = signal["mint"]
                
                if mint in bought_mints or mint in blacklist:
                    continue
                
                if time.time() - signal["ts"] > 10:
                    continue
                
                logger.info(f"SIGNAL: {{signal['name']}} @ +{{signal['peak']:.1f}}%")
                logger.info(f"KELLY BUY: {{mint[:8]}}... | {{KELLY_AMOUNT}} SOL")
                
                bought_mints.add(mint)
                await buy(mint, signal['name'], 0, 0, "")
                
        except Exception as e:
            logger.warning(f"Watch error: {{e}}")
        
        await asyncio.sleep(0.5)

async def main():
    logger.info("BOT B - KELLY FOLLOWER")
    logger.info(f"Kelly: {{KELLY_AMOUNT}} SOL")
    logger.info(f"Trail: +{{TRAILING_STOP_TRIGGER}}% | SL: {{STOP_LOSS_PCT}}%")
    
    await watch_signals()

if __name__ == "__main__":
    asyncio.run(main())
'''

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(bot_b)

print("Bot B built!")
