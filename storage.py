# storage.py - simple SQLite storage for quizzes and results
import sqlite3, json, os
from typing import List, Dict

class QuizStorage:
    def __init__(self, db_path='quizzes.db'):
        self.db_path = db_path
        self._ensure_db()

    def _conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _ensure_db(self):
        c = self._conn()
        cur = c.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS quizzes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, data TEXT)''')
        c.commit()
        c.close()

    def save_quiz(self, name, questions):
        c = self._conn(); cur = c.cursor()
        cur.execute('INSERT INTO quizzes (name,data) VALUES (?,?)', (name, json.dumps({'questions':questions})))
        qid = cur.lastrowid
        c.commit(); c.close()
        return qid

    def get_quiz(self, quiz_id):
        c = self._conn(); cur = c.cursor()
        cur.execute('SELECT data FROM quizzes WHERE id=?', (quiz_id,))
        row = cur.fetchone()
        c.close()
        if not row: return None
        return json.loads(row[0])
