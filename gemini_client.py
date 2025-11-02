# gemini_client.py
# Attempts to call Google Generative Language API if GEMINI_API_KEY provided.
# If no working endpoint is reachable, it returns None (so bot still functions).
import os, json, requests, time

def _call_google_gen(api_key, model, prompt):
    # Try Google Generative API v1beta1 generate endpoint with Bearer token.
    url = f"https://generativelanguage.googleapis.com/v1beta1/models/{model}:generate"
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    payload = {
        "prompt": {"text": prompt},
        "maxOutputTokens": 256
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print('Google call failed:', e)
    return None

def ask_gemini_for_answer(api_key, model, question_text, options):
    """Return 0-based index of predicted correct option or None."""
    if not api_key:
        return None
    # Build a clear prompt asking for the index only.
    prompt = f"You are an expert exam setter. Given the question and options, reply ONLY with the index number (0-based) of the correct option.\nQuestion: {question_text}\nOptions:\n"
    for i,opt in enumerate(options):
        prompt += f"{i}: {opt}\n"
    # First try Google Generative API style endpoint
    data = _call_google_gen(api_key, model, prompt)
    if data:
        # Try extract text from typical response formats
        try:
            # some Google responses contain 'candidates' -> text
            if 'candidates' in data and isinstance(data['candidates'], list) and data['candidates']:
                text = data['candidates'][0].get('output', '') or data['candidates'][0].get('content', '') or ''
            else:
                # nested formats
                text = json.dumps(data)
            for token in text.split():
                if token.strip().isdigit():
                    idx = int(token.strip())
                    if 0 <= idx < len(options):
                        return idx
        except Exception as e:
            print('Parse error:', e)
    # No reliable answer
    return None
