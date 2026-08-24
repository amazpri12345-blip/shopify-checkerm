import os
import time
import math
from collections import Counter
from datetime import datetime

import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

API_URL = os.getenv(
    "RESULT_API_URL",
    "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
)
BOT_TOKEN = os.getenv("8186239066:AAHAEI3fE1WFWyaSsgX0lrp1BSRwmrP_bOE")
HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "100"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))

if not BOT_TOKEN:
    raise RuntimeError("8186239066:AAHAEI3fE1WFWyaSsgX0lrp1BSRwmrP_bOE")


def fetch_history(limit=HISTORY_LIMIT):
    # The website uses a changing timestamp/cache-buster in the request.
    params = {"ts": str(int(time.time() * 1000))}
    r = requests.get(
        API_URL,
        params=params,
        headers={
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0",
        },
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    payload = r.json()

    # Expected shape from the observed response:
    # {"data":{"list":[{"issueNumber":"...","number":"7","color":"green",...}]}}
    data = payload.get("data", {})
    rows = data.get("list", []) if isinstance(data, dict) else []

    if not isinstance(rows, list):
        raise ValueError("Unexpected API response: data.list is not a list")

    cleaned = []
    for row in rows[:limit]:
        if not isinstance(row, dict):
            continue

        issue = row.get("issueNumber")
        number = row.get("number")
        color = row.get("color")

        if issue is None:
            continue

        if isinstance(number, str) and number.isdigit():
            number = int(number)

        if isinstance(color, list):
            color = ",".join(map(str, color))

        cleaned.append({
            "issueNumber": str(issue),
            "number": number,
            "color": str(color).lower() if color is not None else "",
            "premium": row.get("premium"),
            "sum": row.get("sum"),
        })

    return cleaned


def color_counts(rows):
    counts = Counter()
    for row in rows:
        # Some APIs may return "red,violet" etc.; count each listed color.
        for c in row["color"].replace(" ", "").split(","):
            if c in {"red", "green", "violet"}:
                counts[c] += 1
    return counts


def last_streak(rows):
    if not rows:
        return None, 0
    first = rows[0]["color"].split(",")[0].strip().lower()
    if first not in {"red", "green", "violet"}:
        return first, 1

    n = 0
    for row in rows:
        c = row["color"].split(",")[0].strip().lower()
        if c == first:
            n += 1
        else:
            break
    return first, n


def confidence_summary(rows):
    counts = color_counts(rows)
    total = sum(counts.values())
    if total == 0:
        return []

    # This is descriptive frequency, NOT a prediction of the next result.
    result = []
    for color in ("green", "red", "violet"):
        p = counts[color] / total * 100
        result.append((color, counts[color], p))
    result.sort(key=lambda x: x[2], reverse=True)
    return result


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 Colour Statistics Bot\n\n"
        "/stats — frequency statistics\n"
        "/recent — latest results\n"
        "/help — commands\n\n"
        "This bot reports historical frequencies only; it does not guarantee "
        "or claim a future-result prediction."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        rows = fetch_history()
        summary = confidence_summary(rows)
        streak_color, streak_len = last_streak(rows)

        if not summary:
            await update.message.reply_text("No colour data was returned by the API.")
            return

        lines = [
            f"📊 Historical statistics ({len(rows)} rounds)",
            "",
        ]
        for color, count, pct in summary:
            lines.append(f"{color.upper():6} {count:3} rounds — {pct:5.1f}%")

        if streak_color:
            lines += ["", f"Current streak: {streak_color.upper()} × {streak_len}"]

        lines += [
            "",
            "⚠️ These percentages describe the sampled history.",
            "They are not a guaranteed next-round prediction."
        ]
        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"API error: {type(e).__name__}: {e}")


async def recent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        rows = fetch_history(10)
        if not rows:
            await update.message.reply_text("No results returned.")
            return

        lines = ["🧾 Latest 10 results:"]
        for r in rows:
            lines.append(
                f"{r['issueNumber']} → {r['number']} → {r['color']}"
            )
        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"API error: {type(e).__name__}: {e}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("recent", recent))
    print("Bot started.")
    app.run_polling()


if __name__ == "__main__":
    main()
