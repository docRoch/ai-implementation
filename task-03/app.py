import os
import sqlite3
import requests
import uuid
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

import bcrypt
import jwt
from fastapi import FastAPI, HTTPException, Response, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError("Critical Security Error: JWT_SECRET environment variable is not set.")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

ALGORITHM = "HS256"
WINDOW_SIZE = 10
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(CURRENT_DIR, "chat_database.db")

security = HTTPBearer(auto_error=False)

def create_access_token(user_id: int):
    expire = datetime.utcnow() + timedelta(days=7)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[int]:
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except (jwt.PyJWTError, ValueError, TypeError):
        return None

app = FastAPI()

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
            guest_id TEXT,
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

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/session/new")
def create_session(request: Request, response: Response, user_id: Optional[int] = Depends(get_current_user)):
    guest_id = request.cookies.get("guest_id")
    if not user_id and not guest_id:
        guest_id = str(uuid.uuid4())
        response.set_cookie(key="guest_id", value=guest_id, httponly=True, samesite="lax")
    
    session_id = f"sess_{uuid.uuid4().hex}"
    return {"session_id": session_id}

@app.post("/register")
def register(req: RegisterRequest, request: Request, response: Response):
    guest_id = request.cookies.get("guest_id")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            hashed_pwd = bcrypt.hashpw(req.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (req.name, req.email, hashed_pwd),
            )
            user_id = cursor.lastrowid
            
            if guest_id:
                cursor.execute(
                    "UPDATE chats SET user_id = ?, guest_id = NULL WHERE user_id IS NULL AND guest_id = ?",
                    (user_id, guest_id),
                )
            conn.commit()
            
            if guest_id:
                response.delete_cookie("guest_id")
                
            token = create_access_token(user_id)
            return {"user_id": user_id, "name": req.name, "access_token": token}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="This email is already registered.")

@app.post("/login")
def login(req: LoginRequest, request: Request, response: Response):
    guest_id = request.cookies.get("guest_id")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, password FROM users WHERE email = ?", (req.email,))
        row = cursor.fetchone()
        if not row or not bcrypt.checkpw(req.password.encode("utf-8"), row[2].encode("utf-8")):
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        
        user_id = row[0]
        if guest_id:
            cursor.execute(
                "UPDATE chats SET user_id = ?, guest_id = NULL WHERE user_id IS NULL AND guest_id = ?",
                (user_id, guest_id),
            )
            conn.commit()
            response.delete_cookie("guest_id")
            
        token = create_access_token(user_id)
        return {"user_id": user_id, "name": row[1], "access_token": token}

@app.get("/history/{session_id}")
def get_history(session_id: str, request: Request, user_id: Optional[int] = Depends(get_current_user)):
    guest_id = request.cookies.get("guest_id")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, guest_id FROM chats WHERE session_id = ? LIMIT 1", (session_id,))
        row = cursor.fetchone()
        
        if row:
            owner_user_id, owner_guest_id = row[0], row[1]
            if owner_user_id is not None and owner_user_id != user_id:
                raise HTTPException(status_code=403, detail="Unauthorized")
            if owner_user_id is None and (not guest_id or owner_guest_id != guest_id):
                raise HTTPException(status_code=403, detail="Unauthorized")
                
        cursor.execute("SELECT role, content FROM chats WHERE session_id = ? ORDER BY id ASC", (session_id,))
        rows = cursor.fetchall()
        return {"history": [{"role": r[0], "content": r[1]} for r in rows]}

@app.post("/chat")
def ask_ai(req: ChatRequest, request: Request, response: Response, user_id: Optional[int] = Depends(get_current_user)):
    guest_id = request.cookies.get("guest_id")
    if not user_id and not guest_id:
        guest_id = str(uuid.uuid4())
        response.set_cookie(key="guest_id", value=guest_id, httponly=True, samesite="lax")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, guest_id FROM chats WHERE session_id = ? LIMIT 1", (req.session_id,))
            existing_session = cursor.fetchone()
            
            if existing_session:
                owner_user_id, owner_guest_id = existing_session[0], existing_session[1]
                if owner_user_id is not None and owner_user_id != user_id:
                    raise HTTPException(status_code=403, detail="Unauthorized access to this chat session.")
                if owner_user_id is None and (not guest_id or owner_guest_id != guest_id):
                    raise HTTPException(status_code=403, detail="Unauthorized access to this chat session.")
            else:
                if not user_id:
                    cursor.execute(
                        "SELECT COUNT(DISTINCT session_id) FROM chats WHERE user_id IS NULL AND guest_id = ?",
                        (guest_id,),
                    )
                    if cursor.fetchone()[0] >= 3:
                        raise HTTPException(status_code=403, detail="LOGIN_REQUIRED")

            effective_guest_id = guest_id if not user_id else None
            cursor.execute(
                "INSERT INTO chats (session_id, user_id, guest_id, role, content) VALUES (?, ?, ?, 'user', ?)",
                (req.session_id, user_id, effective_guest_id, req.prompt),
            )
            conn.commit()

            cursor.execute(
                "SELECT role, content FROM chats WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (req.session_id, WINDOW_SIZE),
            )
            rows = cursor.fetchall()
            context_window = [{"role": r[0], "content": r[1]} for r in reversed(rows)]

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-OpenRouter-Title": "LocalAPI",
        }
        payload = {
            "model": "~openai/gpt-sol-latest",
            "max_tokens": 300,
            "messages": context_window,
        }
        res = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.text)
        
        data = res.json()
        if "choices" not in data or len(data["choices"]) == 0:
            raise HTTPException(status_code=500, detail="Invalid response from AI provider.")
            
        ai_reply = data["choices"][0]["message"]["content"]

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chats (session_id, user_id, guest_id, role, content) VALUES (?, ?, ?, 'assistant', ?)",
                (req.session_id, user_id, effective_guest_id, ai_reply),
            )
            conn.commit()
            
        return {"response": ai_reply}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"API Request failed: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.delete("/chat/{session_id}")
def delete_chat(session_id: str, request: Request, user_id: Optional[int] = Depends(get_current_user)):
    guest_id = request.cookies.get("guest_id")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, guest_id FROM chats WHERE session_id = ? LIMIT 1", (session_id,))
        row = cursor.fetchone()
        if row:
            owner_user_id, owner_guest_id = row[0], row[1]
            if owner_user_id is not None and owner_user_id != user_id:
                raise HTTPException(status_code=403, detail="Unauthorized")
            if owner_user_id is None and (not guest_id or owner_guest_id != guest_id):
                raise HTTPException(status_code=403, detail="Unauthorized")
                
        cursor.execute("DELETE FROM chats WHERE session_id = ?", (session_id,))
        conn.commit()
    return {"status": "deleted"}

@app.get("/user/chats")
def get_user_chats(user_id: Optional[int] = Depends(get_current_user)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT session_id, content 
            FROM chats 
            WHERE user_id = ? AND role = 'user' 
            GROUP BY session_id 
            ORDER BY MIN(id) ASC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        chats = [
            {
                "id": r[0],
                "name": (r[1][:25] + "...") if len(r[1]) > 25 else r[1],
                "pinned": False,
            }
            for r in rows
        ]
        return {"chats": chats}

app.mount("/", StaticFiles(directory=CURRENT_DIR, html=True), name="static")