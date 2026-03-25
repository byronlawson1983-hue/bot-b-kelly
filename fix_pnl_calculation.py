with open("PYTHON_BOT_B_KELLY_ONLY.py", "r") as f:
    content = f.read()

# Replace market cap PnL with bonding curve PnL (like Bot A)
old = '''            current_mc=d.get('marketCapSol',0)
            entry_mc=p["entry_mc"]
            p["last_trade_time"]=time.time()
            
            if current_mc>0 and entry_mc>0:
                pnl=((current_mc-entry_mc)/entry_mc)*100'''

new = '''            current_bonding=d.get('progress',0)  # Bonding curve %
            entry_bonding=p.get("entry_bonding",0)
            p["last_trade_time"]=time.time()
            
            if current_bonding>0 and entry_bonding>0:
                pnl=((current_bonding-entry_bonding)/entry_bonding)*100'''

content = content.replace(old, new)

with open("PYTHON_BOT_B_KELLY_ONLY.py", "w") as f:
    f.write(content)

print("✅ Fixed PnL to use bonding curve instead of market cap")
