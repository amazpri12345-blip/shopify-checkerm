# Okwin Historical Colour Statistics Telegram Bot

This bot fetches historical WinGo 1-minute results from the endpoint observed in
Chrome DevTools and reports descriptive statistics.

## 1. Install

Ubuntu/Debian VPS:

```bash
sudo apt update
sudo apt install -y python3 python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Create a Telegram bot

Use Telegram's official BotFather to create a bot and copy its bot token.

Set it in the shell:

```bash
export BOT_TOKEN="PASTE_YOUR_TELEGRAM_BOT_TOKEN_HERE"
```

Optional settings:

```bash
export HISTORY_LIMIT=100
export RESULT_API_URL="https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
```

## 3. Run

```bash
python bot.py
```

Commands:

- `/start`
- `/stats`
- `/recent`
- `/help`

## Important

The API response observed during setup contains fields such as
`issueNumber`, `number`, and `color`. The parser expects them under
`data.list`.

The `/stats` command calculates historical colour frequencies. It does not
claim that the most frequent colour is the next result, and it does not
guarantee 95% accuracy.

Do not put cookies, Authorization headers, session tokens, passwords, or other
private credentials into the source code.
