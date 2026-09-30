from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

class ChatRequest(BaseModel):
    prompt: str

@app.post("/chat")
def ask_ai(req: ChatRequest):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",
        "X-OpenRouter-Title": "LocalAPI"
    }

    payload = {
        "model": "~openai/gpt-sol-latest",
        "max_tokens": 300,
        "messages": [
            {"role": "user", "content": req.prompt}
        ]
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
        data = response.json()
        ai_reply = data["choices"][0]["message"]["content"]
        
        return {"response": ai_reply}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))