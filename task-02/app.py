import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

chat_history = []

class ChatRequest(BaseModel):
    prompt: str

@app.post("/chat")
def ask_ai(req: ChatRequest):
    chat_history.append({"role": "user", "content": req.prompt})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",
        "X-OpenRouter-Title": "LocalAPI"
    }

    payload = {
        "model": "~openai/gpt-sol-latest",
        "max_tokens": 300,
        "messages": chat_history
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            chat_history.pop()
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
        data = response.json()
        ai_reply = data["choices"][0]["message"]["content"]
        
        chat_history.append({"role": "assistant", "content": ai_reply})
        
        return {"response": ai_reply}

    except requests.exceptions.RequestException as e:
        chat_history.pop()
        raise HTTPException(status_code=500, detail=str(e))