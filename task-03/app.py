import os
import sqlite3
import requests
from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(CURRENT_DIR, "chat_database.db")
WINDOW_SIZE = 10

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_id INTEGER,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    return conn

class ChatRequest(BaseModel):
    prompt: str
    session_id: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    guest_id: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str
    guest_id: Optional[str] = None

@app.post("/register")
def register(req: RegisterRequest):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                           (req.name, req.email, req.password))
            user_id = cursor.lastrowid
            
            # انتقال تمام چت‌های این مهمان به حساب کاربری جدید
            if req.guest_id:
                cursor.execute("UPDATE chats SET user_id = ? WHERE user_id IS NULL AND session_id LIKE ?", 
                               (user_id, f"sess_{req.guest_id}_%"))
                
            conn.commit()
            return {"user_id": user_id, "name": req.name}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="This email is already registered.")

@app.post("/login")
def login(req: LoginRequest):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM users WHERE email = ? AND password = ?", (req.email, req.password))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
            
        user_id = row[0]
        
        # انتقال تمام چت‌های این مهمان به حساب کاربری لاگین شده
        if req.guest_id:
            cursor.execute("UPDATE chats SET user_id = ? WHERE user_id IS NULL AND session_id LIKE ?", 
                           (user_id, f"sess_{req.guest_id}_%"))
            conn.commit()
            
        return {"user_id": user_id, "name": row[1]}

@app.get("/history/{session_id}")
def get_history(session_id: str, x_user_id: Optional[str] = Header(default=None)):
    user_id = int(x_user_id) if x_user_id and x_user_id.isdigit() else None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM chats WHERE session_id = ? LIMIT 1", (session_id,))
        row = cursor.fetchone()
        
        if row and row[0] is not None and row[0] != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
            
        cursor.execute("SELECT role, content FROM chats WHERE session_id = ? ORDER BY id ASC", (session_id,))
        rows = cursor.fetchall()
        return {"history": [{"role": r[0], "content": r[1]} for r in rows]}

@app.post("/chat")
def ask_ai(req: ChatRequest, x_user_id: Optional[str] = Header(default=None)):
    user_id = int(x_user_id) if x_user_id and x_user_id.isdigit() else None

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT user_id FROM chats WHERE session_id = ? LIMIT 1", (req.session_id,))
            existing_session = cursor.fetchone()

            if existing_session:
                if existing_session[0] is not None and existing_session[0] != user_id:
                    raise HTTPException(status_code=403, detail="Unauthorized access to this chat session.")
            else:
                if not user_id:
                    parts = req.session_id.split('_')
                    if len(parts) >= 3:
                        guest_id = parts[1]
                        cursor.execute("SELECT COUNT(DISTINCT session_id) FROM chats WHERE user_id IS NULL AND session_id LIKE ?", (f"sess_{guest_id}_%",))
                        if cursor.fetchone()[0] >= 3:
                            raise HTTPException(status_code=403, detail="LOGIN_REQUIRED")

            cursor.execute("INSERT INTO chats (session_id, user_id, role, content) VALUES (?, ?, 'user', ?)",
                           (req.session_id, user_id, req.prompt))
            conn.commit()

            cursor.execute("SELECT role, content FROM chats WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                           (req.session_id, WINDOW_SIZE))
            rows = cursor.fetchall()
            context_window = [{"role": r[0], "content": r[1]} for r in reversed(rows)]

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

        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()
        if "choices" not in data or len(data["choices"]) == 0:
            raise HTTPException(status_code=500, detail="Invalid response from AI provider.")
            
        ai_reply = data["choices"][0]["message"]["content"]

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO chats (session_id, user_id, role, content) VALUES (?, ?, 'assistant', ?)",
                           (req.session_id, user_id, ai_reply))
            conn.commit()

        return {"response": ai_reply}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"API Request failed: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.delete("/chat/{session_id}")
def delete_chat(session_id: str, x_user_id: Optional[str] = Header(default=None)):
    user_id = int(x_user_id) if x_user_id and x_user_id.isdigit() else None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM chats WHERE session_id = ? LIMIT 1", (session_id,))
        row = cursor.fetchone()
        
        if row and row[0] is not None and row[0] != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
            
        cursor.execute("DELETE FROM chats WHERE session_id = ?", (session_id,))
        conn.commit()
    return {"status": "deleted"}

@app.get("/user/chats")
def get_user_chats(x_user_id: Optional[str] = Header(default=None)):
    user_id = int(x_user_id) if x_user_id and x_user_id.isdigit() else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT session_id, content 
            FROM chats 
            WHERE user_id = ? AND role = 'user' 
            GROUP BY session_id 
            ORDER BY MIN(id) ASC
        """, (user_id,))
        rows = cursor.fetchall()
        
        chats = [{"id": r[0], "name": (r[1][:25] + "...") if len(r[1]) > 25 else r[1], "pinned": False} for r in rows]
        return {"chats": chats}

app.mount("/", StaticFiles(directory=CURRENT_DIR, html=True), name="static")