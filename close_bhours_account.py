import subprocess
import json

# Load wallet securely using ansible-vault
result = subprocess.run(
    ['ansible-vault', 'view', '.env'],
    capture_output=True,
    text=True,
    env={'ANSIBLE_VAULT_PASSWORD_FILE': '/dev/stdin'},
    input=subprocess.run(['cat'], capture_output=True, text=True).stdout
)

env_data = {}
for line in result.stdout.split('\n'):
    if '=' in line:
        key, value = line.split('=', 1)
        env_data[key] = value.strip()

wallet_key = env_data['WALLET_PRIVATE_KEY']

# Close token account using spl-token CLI
mint = "3JNPaqSF9rXSpoKuek8HaMgwrtzPjByJRZJ8HgqTpump"

print(f"Closing token account for {mint[:8]}...")
print("This will recover ~0.002 SOL rent")

# Use spl-token close command
result = subprocess.run([
    'spl-token', 'close', '--address', mint,
    '--owner', wallet_key
], capture_output=True, text=True)

print(result.stdout)
if result.returncode == 0:
    print("✅ Account closed, rent recovered!")
else:
    print(f"❌ Error: {result.stderr}")
