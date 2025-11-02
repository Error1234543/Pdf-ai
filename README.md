# Render-ready Polling-mode AI PDF → Quiz Bot

This repo is ready to deploy on Render as a Web Service and runs in POLLING mode (bot.infinity_polling()).
It includes a tiny health server so Render treats the service as alive.

## Environment variables (set these in Render dashboard)
- TELEGRAM_BOT_TOKEN (required)
- GEMINI_API_KEY (optional — Google Generative / Gemini API key)
- GEMINI_MODEL (optional, default: gemini-1.5-flash)
- ADMIN_ID (optional)

## Build & Start commands on Render
Build command:
pip install -r requirements.txt

Start command:
python3 bot.py

Notes:
- If you want the bot to label answers automatically, provide a valid Google Generative API key.
- For Gujarati OCR, install Gujarati traineddata for tesseract on the host.
- The bot stores quizzes in local SQLite database `quizzes.db`.
