#!/bin/bash
cd /root/bot-b-kelly
ansible-vault decrypt .env --vault-password-file <(echo 'bot-b-secure-vault-2026-v2') --output /tmp/bot_b.env
export $(grep -v '^#' /tmp/bot_b.env | xargs)
rm /tmp/bot_b.env
python3 PYTHON_BOT_B_KELLY_ONLY.py
