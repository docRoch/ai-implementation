# Task 01 — Custom AI Gateway API

English | [فارسی](README_FA.md)

- **Duration**: 16 Sep 2026 – 19 Sep 2026
- **Files**: `main.py`, `apiapp.py`


### Build a custom AI API accepting only POST requests

Wrong task I started with: Write a code to connect to an LLM via API (OpenAI compatible)

First of all, I used a Gemini API key from Google AI Studio and the openai library in Python. I got errors and spent 2 hours trying to understand what the problem was, but I figured out Google servers were the issue.

After that, I used OpenRouter APIs and the openai library. The connection (request and response) was successful. I used the gpt-sol-latest model.

This was the start, and now I'm refactoring the code to understand exactly what each part does.

After connecting directly to the LLM via script, the next objective was to expose our own web service rather than just consuming an external API.

I implemented a REST API using FastAPI and Uvicorn. The service defines an endpoint (/chat) that strictly accepts HTTP POST requests containing a user prompt, forwards the payload to the LLM provider, and returns the response. Any other HTTP methods (such as GET) are rejected automatically with a 405 Method Not Allowed status.

API Core Concepts & Takeaways:

An API is fundamentally a request-response communication mechanism between two distinct services (client-to-server or server-to-server). An endpoint serves as the specific destination URL where incoming traffic is handled by routing functions.

Each outgoing request contains Headers (used for token-based authentication and metadata) and a Payload (the request body defining what we need). Based on OpenRouter's documentation, we specify parameters like model, max_tokens, and the messages array (containing role and the actual prompt) inside this payload.

Inside the try-except block, we dispatch the HTTP POST request to OpenRouter. The resulting response object provides the HTTP status code (e.g., 200 for success), response headers, raw text, and the .json() method to parse the payload into a Python dictionary.

From OpenRouter's structured response dictionary—which returns fields like id, model, choices, and usage—we extract the AI's generated response directly from choices[0].message.content.