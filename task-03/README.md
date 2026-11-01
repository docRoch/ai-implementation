# Task 03 — Full-Stack Web Chatbot

English | [فارسی](README_FA.md)

- **Duration**: 28 Sep 2026 – 02 Oct 2026 (Completed)
- **Files**: `app.py`, `index.html`, `script.js`, `style.css`, `chat_database.db`, `chatbot-icon.svg`

### Full-Stack Web Chatbot with Session & User Management

The goal of this task is to migrate the backend-only chatbot from Task 02 into a fully functional, modern web application. This involves building a full-stack environment with a clear separation of concerns using HTML, CSS (Tailwind), vanilla JavaScript for the frontend, and a FastAPI backend with SQLite for persistent data storage.

A major focus of this implementation is **Security and Chat Isolation**. The system utilizes dynamic session IDs and user authentication to ensure that chat histories are strictly isolated per user and per browser. Guests can start chatting immediately without creating an account, with their temporary data tracked via a `guest_id` stored in the browser's `localStorage`.

To manage resources and drive user acquisition, a **Guest Quota System** was introduced. Unauthenticated users are allowed to create a maximum of 3 free chat sessions. Upon attempting to interact beyond this limit, the system triggers an authentication modal requiring the user to log in or register. 

Crucially, the user experience remains uninterrupted: once a guest successfully registers or logs in, the backend seamlessly **migrates all previously created guest chats** to their authenticated account. The UI mimics modern AI interfaces, featuring a sidebar for session management (with pin, rename, and delete capabilities), full Markdown rendering for AI responses, and custom Toast notifications for smooth, non-intrusive error handling.