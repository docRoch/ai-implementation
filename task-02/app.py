import json
import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
HISTORY_FILE = "chat_history.json"
WINDOW_SIZE = 10 # the last 5 prompts of user + 5 answer of ai = 10

def load_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_history(history: list):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

class ChatRequest(BaseModel):
    prompt: str

@app.post("/chat")
def ask_ai(req: ChatRequest):
    chat_history = load_history()
    chat_history.append({"role": "user", "content": req.prompt})
    context_window = chat_history[-WINDOW_SIZE:]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",
        "X-OpenRouter-Title": "LocalAPI"
    }

    payload = {
        "model": "~openai/gpt-sol-latest",
        "max_tokens": 300,
        "messages": context_window
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
        data = response.json()
        ai_reply = data["choices"][0]["message"]["content"]
        
        chat_history.append({"role": "assistant", "content": ai_reply})
        save_history(chat_history)
        
        return {"response": ai_reply}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))