### This is a markdown file for notes and writing task activities.

---

## Task 01

- Duration:
    - Start: 16 Sep 2026
    - End: not yet

- Files:
    - main.py
    - apiapp.py


### Build a custom AI API accepting only POST requests

Wrong task I started with: Write a code to connect to an LLM via API (OpenAI compatible)

First of all, I used a Gemini API key from Google AI Studio and the openai library in Python. I got errors and spent 2 hours trying to understand what the problem was, but I figured out Google servers were the issue.

After that, I used OpenRouter APIs and the openai library. The connection (request and response) was successful. I used the gpt-sol-latest model.

This was the start, and now I'm refactoring the code to understand exactly what each part does.

After connecting directly to the LLM via script, the next objective was to expose our own web service rather than just consuming an external API.

I implemented a REST API using FastAPI and Uvicorn. The service defines an endpoint (/chat) that strictly accepts HTTP POST requests containing a user prompt, forwards the payload to the LLM provider, and returns the response. Any other HTTP methods (such as GET) are rejected automatically with a 405 Method Not Allowed status.