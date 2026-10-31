# AI Implementation Engineering Suite

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Database: SQLite](https://img.shields.io/badge/Database-SQLite-003B57.svg?logo=sqlite&logoColor=white)](https://sqlite.org)
[![Tailwind CSS](https://img.shields.io/badge/UI-Tailwind_CSS-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)

English | [فارسی](README_FA.md)

A progressive, hands-on engineering repository demonstrating real-world Large Language Model (LLM) system design using **Python**, **FastAPI**, **SQLite**, and modern frontend web technologies.

---

## Overview

Building production AI software requires far more than basic API prompts. This repository progresses step-by-step from raw API integration and robust error handling to application-managed conversational memory, culminating in a full-stack chatbot with authenticated user sessions, guest quotas, and dynamic UI management.

Key highlights:
- **Zero Vendor Lock-In**: Application-managed memory windows instead of costly provider-managed stateful threads.
- **Defensive API Architecture**: Strict HTTP method whitelisting (405 Method Not Allowed), structured schema validation, and error boundaries.
- **Full-Stack Architecture**: Clean separation between FastAPI backend endpoints, persistent SQLite storage, and a responsive glassmorphic UI.
- **Guest-to-User State Migration**: Seamlessly transfers guest trial history to authenticated accounts upon login.

---

## Tasks Breakdown

| Task | Name | Focus | Tech Stack |
| :--- | :--- | :--- | :--- |
| [`task-01`](task-01/) | **Custom AI Gateway API** | POST-only `/chat` endpoint with OpenRouter integration, strict method validation, and headers | FastAPI, OpenRouter, Uvicorn |
| [`task-02`](task-02/) | **Conversational Memory** | Sliding-window context management (10-message rolling window: 5 user + 5 assistant turns) | FastAPI, Pydantic, In-Memory Store |
| [`task-03`](task-03/) | **Full-Stack Web Chatbot** | Multi-session chat app, guest quota (3 trial sessions), user auth & migration, sidebar session controls | FastAPI, SQLite, Vanilla JS, Tailwind CSS |

---

### 1. `task-01`: Custom AI Gateway API
* Connects directly to OpenRouter API to forward user prompts to top-tier LLM models.
* Strictly enforces HTTP `POST` requests on `/chat`, blocking unauthorized methods with clear `405 Method Not Allowed` responses.
* Implements robust error handling for API timeouts and upstream connectivity issues.

### 2. `task-02`: Sliding-Window Conversational Memory
* Solves the stateless nature of LLMs via **Application-Managed Memory**.
* Adopts a configurable **Sliding Window** strategy retaining the last 10 messages (5 user prompts and 5 assistant replies).
* Eliminates vendor thread storage fees while keeping context window sizes and API token costs bounded and predictable.

### 3. `task-03`: Full-Stack Web Chatbot with Session Management
* Complete web interface with responsive sidebar session management (pin, rename, delete sessions).
* **Guest Quota & Seamless Migration**: Allows guests up to 3 trial chat sessions, migrating temporary discussions into their persistent account upon signup/login.
* Full Markdown formatting with syntax highlighting and toast notifications.

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- An OpenRouter API key (or compatible OpenAI-format API endpoint)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/docRoch/ai-implementation.git
   cd ai-implementation
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   # Edit .env and insert your OPENROUTER_API_KEY
   ```

### Running Tasks

- **Run Task 01 API**:
  ```bash
  cd task-01
  python main.py
  ```

- **Run Task 02 Conversational Memory**:
  ```bash
  cd task-02
  python app.py
  ```

- **Run Task 03 Full-Stack Chatbot**:
  ```bash
  cd task-03
  python app.py
  # Open http://localhost:8000 in your browser
  ```

---

## Project Structure

```text
ai-implementation/
├── requirements.txt        # Shared Python dependencies
├── .env.example            # Environment variables template
├── task-01/                # Task 01: Custom POST-only API
│   ├── apiapp.py
│   ├── main.py
│   └── README.md
├── task-02/                # Task 02: Sliding window conversational memory
│   ├── app.py
│   └── README.md
└── task-03/                # Task 03: Full-stack chatbot web application
    ├── app.py              # FastAPI server & SQLite database operations
    ├── index.html          # Chat interface
    ├── script.js           # Client-side state, session management, and UI logic
    ├── style.css           # Styling
    └── README.md
```

---

## Contributing

Contributions, bug reports, and suggestions are welcome!
1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/cool-enhancement`).
3. Commit your changes (`git commit -m 'Add cool enhancement'`).
4. Push to the branch (`git push origin feature/cool-enhancement`).
5. Open a Pull Request.

---

## License

This project is licensed under the [MIT License](LICENSE).

