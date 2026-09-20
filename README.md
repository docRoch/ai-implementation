# AI Implementation
An AI implementation project

## Tasks

### Task 01

#### Build a custom AI API accepting only POST requests

In Task 01, I connected to OpenRouter and built a custom API using FastAPI. The service has a /chat endpoint that only accepts POST requests, sends the user prompt with the required headers and settings to the AI model, and returns the response while blocking any other HTTP methods with a 405 error.