# pdf_extract.py
# Utilities to extract text and MCQ-like questions from PDFs.
# Uses PyMuPDF (fitz) and pytesseract (for scanned pages).
import os, re, tempfile
from typing import List, Dict

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

from PIL import Image
import pytesseract
from pdf2image import convert_from_path

# Simple heuristic-based extractor: finds lines ending with '?', then subsequent lines as options.
def extract_questions_from_pdf(path: str) -> List[Dict]:
    text = ''
    questions = []
    # First, try to extract with PyMuPDF
    if fitz:
        doc = fitz.open(path)
        for page in doc:
            text += page.get_text()
    if not text.strip():
        # fallback to OCR each page
        images = convert_from_path(path, dpi=200)
        for img in images:
            text += pytesseract.image_to_string(img, lang='eng+guj')  # requires guj traineddata
    # Normalize and split by lines
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    i = 0
    while i < len(lines):
        line = lines[i]
        # naive question detection: contains '?' or starts with Q or digits + '.'
        if '?' in line or re.match(r'^(Q|q)?\d+[\).]', line) or re.search(r'^(Which|Choose|Who|What|કોણ|ક્યો)', line):
            qtext = re.sub(r'^\d+[\)\.]\s*', '', line).strip()
            i += 1
            options = []
            # collect up to 6 following option-like lines (start with A. (A) or similar)
            while i < len(lines) and len(options) < 6:
                ol = lines[i]
                if re.match(r'^[A-D][\.\)]\s*', ol) or re.match(r'^\([A-D]\)', ol) or re.match(r'^[A-D]\s+-', ol) or len(options)<1 and re.match(r'^[a-d]\)', ol, re.I):
                    # clean prefix
                    opt = re.sub(r'^[A-Da-d][\.\)\-]\s*', '', ol)
                    options.append(opt)
                    i += 1
                else:
                    # or if line looks like an option without label (short)
                    if len(ol.split()) < 6 and len(options)>0:
                        options.append(ol); i+=1
                    else:
                        break
            questions.append({'question': qtext, 'options': options})
        else:
            i += 1
    # Optionally, try to detect answers from answer key at end (Ans: B or Answer key)
    # simple scan for patterns like 'Ans: B' or 'Answer: (B)'
    answer_map = {}
    for idx,line in enumerate(lines[-50:], start=max(0,len(lines)-50)):
        m = re.search(r'Ans(?:wer)?[:\s]*\(?([A-D])\)?', lines[idx], re.I)
        if m:
            # if there's numbering earlier, try to map by index order; here we just append sequentially
            answer_map[len(answer_map)] = ord(m.group(1).upper()) - 65
    # assign answer indices if counts match
    if answer_map and len(answer_map)==len(questions):
        for i,a in answer_map.items():
            questions[i]['answer_index'] = a
    else:
        # Try using AI to detect correct answer (only if GEMINI configured) - placeholder handled by bot flow
        pass
    return questions
