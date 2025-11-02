#!/usr/bin/env python3
# Simple Telegram Quiz Bot (Termux-friendly)
# Usage: set environment variable TELEGRAM_BOT_TOKEN and GEMINI_API_KEY (if using Gemini)
# Run: python3 bot.py

import os
import time
import json
import threading
from pathlib import Path

import telebot

from pdf_extract import extract_questions_from_pdf
from storage import QuizStorage
from gemini_client import ask_gemini_for_answer, analyze_and_split_questions

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN') or 'REPLACE_WITH_YOUR_TOKEN'
ADMIN_ID = int(os.environ.get('ADMIN_ID') or 0)

bot = telebot.TeleBot(BOT_TOKEN)
storage = QuizStorage(db_path='quizzes.db')

# stages: when user uploads pdf, create quiz and send questions sequentially
user_sessions = {}  # chat_id -> {'quiz_id':..., 'qindex':..., 'answers':[]}

@bot.message_handler(commands=['start'])
def start_cmd(msg):
    bot.reply_to(msg, "Send me a PDF (scanned or text). I will convert it to a quiz (English + Gujarati supported). Admin only upload if configured. After quiz, send /result to see score.")

@bot.message_handler(content_types=['document'])
def handle_document(msg):
    doc = msg.document
    if not doc.file_name.lower().endswith('.pdf'):
        bot.reply_to(msg, "Please send a PDF file.")
        return
    file_info = bot.get_file(doc.file_id)
    downloaded = bot.download_file(file_info.file_path)
    path = f"uploads/{doc.file_name}"
    os.makedirs("uploads", exist_ok=True)
    with open(path, "wb") as f:
        f.write(downloaded)
    bot.reply_to(msg, f"PDF received. Extracting questions...")
    try:
        qlist = extract_questions_from_pdf(path)
        if not qlist:
            bot.reply_to(msg, "Could not find questions automatically. Make sure the PDF contains MCQs in clear format.")
            return
        quiz_id = storage.save_quiz(doc.file_name, qlist)
        bot.reply_to(msg, f"Quiz created with {len(qlist)} questions. Use /take_{quiz_id} to start taking it.")
        # auto-start for uploader
        start_quiz_for_user(msg.chat.id, quiz_id)
    except Exception as e:
        bot.reply_to(msg, f"Error extracting PDF: {e}")

def start_quiz_for_user(chat_id, quiz_id):
    quiz = storage.get_quiz(quiz_id)
    if not quiz: return
    user_sessions[chat_id] = {'quiz_id': quiz_id, 'qindex': 0, 'answers': []}
    send_next_question(chat_id)

def send_next_question(chat_id):
    session = user_sessions.get(chat_id)
    if not session: return
    quiz = storage.get_quiz(session['quiz_id'])
    idx = session['qindex']
    if idx >= len(quiz['questions']):
        bot.send_message(chat_id, "Quiz finished! Send /result to see your results.")
        return
    q = quiz['questions'][idx]
    text = f"Q{idx+1}. {q['question']}\n\n"
    opts = q.get('options', [])
    kb = telebot.types.InlineKeyboardMarkup()
    for i,opt in enumerate(opts):
        kb.add(telebot.types.InlineKeyboardButton(text=f"{chr(65+i)}. {opt}", callback_data=f"ans|{idx}|{i}"))
    bot.send_message(chat_id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith('ans|'))
def on_answer(call):
    parts = call.data.split('|')
    qidx = int(parts[1]); optidx = int(parts[2])
    chat_id = call.message.chat.id
    session = user_sessions.get(chat_id)
    if not session:
        bot.answer_callback_query(call.id, "Session expired. Start quiz again.")
        return
    session['answers'].append({'q': qidx, 'selected': optidx})
    session['qindex'] += 1
    bot.answer_callback_query(call.id, f"Recorded answer {chr(65+optidx)}")
    send_next_question(chat_id)

@bot.message_handler(commands=['result'])
def show_result(msg):
    chat_id = msg.chat.id
    session = user_sessions.get(chat_id)
    if not session:
        bot.reply_to(msg, "No active quiz session found. Use the /take_<id> command to start.")
        return
    quiz = storage.get_quiz(session['quiz_id'])
    answers = session['answers']
    correct_map = {i: q.get('answer_index') for i,q in enumerate(quiz['questions'])}
    lines = []
    score = 0
    for i in range(len(quiz['questions'])):
        sel = next((a['selected'] for a in answers if a['q']==i), None)
        is_correct = (sel is not None and correct_map.get(i) is not None and sel==correct_map[i])
        lines.append(f"{i+1}. {'✅' if is_correct else '❌'}")
        if is_correct: score += 1
    lines.append(f"\nScore: {score} / {len(quiz['questions'])}")
    bot.send_message(chat_id, "\n".join(lines))

# Admin helper to force take a quiz: /take_<id>
@bot.message_handler(func=lambda m: m.text and m.text.startswith('/take_'))
def take_cmd(msg):
    try:
        quiz_id = int(msg.text.split('_',1)[1])
        start_quiz_for_user(msg.chat.id, quiz_id)
    except Exception as e:
        bot.reply_to(msg, "Invalid command. Use /take_<quizid>")

if __name__ == '__main__':
    print("Bot is polling...")
    bot.infinity_polling()
