# pdf_extract.py
# Utilities to extract text and MCQ-like questions from PDFs.
import os, re
from typing import List, Dict
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

def extract_questions_from_pdf(path: str) -> List[Dict]:
    text = ''
    questions = []
    if fitz:
        try:
            doc = fitz.open(path)
            for page in doc:
                text += page.get_text()
        except Exception:
            text = ''
    if not text.strip():
        images = convert_from_path(path, dpi=200)
        for img in images:
            try:
                text += pytesseract.image_to_string(img, lang='eng+guj')
            except Exception:
                text += pytesseract.image_to_string(img)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    i = 0
    while i < len(lines):
        line = lines[i]
        if '?' in line or re.match(r'^(Q|q)?\d+[\).]', line) or re.search(r'^(Which|Choose|Who|What|કોણ|ક્યો)', line):
            qtext = re.sub(r'^\d+[\)\.]\s*', '', line).strip()
            i += 1
            options = []
            while i < len(lines) and len(options) < 6:
                ol = lines[i]
                if re.match(r'^[A-D][\.)]\s*', ol) or re.match(r'^\([A-D]\)', ol) or re.match(r'^[A-D]\s+-', ol) or (len(ol.split()) < 10 and re.match(r'^[a-d]\)', ol, re.I)):
                    opt = re.sub(r'^[A-Da-d][\.)\-]\s*', '', ol)
                    options.append(opt)
                    i += 1
                else:
                    if len(ol.split()) < 6 and len(options)>0:
                        options.append(ol); i+=1
                    else:
                        break
            questions.append({'question': qtext, 'options': options})
        else:
            i += 1
    tail = lines[-200:] if len(lines)>200 else lines
    answer_map = {}
    for ln in tail:
        m = re.search(r'Ans(?:wer)?[:\s]*\(?([A-D])\)?', ln, re.I)
        if m:
            answer_map[len(answer_map)] = ord(m.group(1).upper()) - 65
    if answer_map and len(answer_map)==len(questions):
        for i,a in answer_map.items():
            questions[i]['answer_index'] = a
    return questions
