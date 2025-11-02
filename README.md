# AI PDF → Quiz Bot (Termux friendly)

This package contains a lightweight Telegram bot that converts PDF files into interactive quizzes.
It supports both English and Gujarati text (OCR requires Gujarati traineddata for Tesseract).

## Setup (Termux)
1. Install system dependencies:
   ```bash
   pkg update && pkg upgrade -y
   pkg install python ffmpeg tesseract imagemagick poppler -y
   pip install --upgrade pip
   ```
2. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Place your Telegram bot token in environment variable:
   ```bash
   export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
   export GEMINI_API_KEY="YOUR_GEMINI_PI_KEY"  # optional for AI answers
   export ADMIN_ID="YOUR_TELEGRAM_USER_ID"     # optional
   ```
4. Run the bot:
   ```bash
   python3 bot.py
   ```

## Gemini Pi Integration
- `gemini_client.py` contains a placeholder. Replace `ask_gemini_for_answer` with your Gemini Pi / Google Generative API implementation.
- Alternatively, keep it empty: the bot uses heuristic extraction from the PDF and will create a quiz without AI-labeled correct answers. You can later add `answer_index` manually or extend `gemini_client`.

## Notes & Tips
- For OCR Gujarati support, install Gujarati `tesseract` traineddata file.
- The extractor is heuristic-based and works best with clearly formatted MCQs.
- After upload, the bot auto-creates a quiz and prompts to start. Use `/take_<quizid>` to begin if needed.
- Use `/result` to view your score as simple text.

