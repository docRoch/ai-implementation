# AI Implementation
An AI implementation project

## Tasks

### Task 01

#### Build a custom AI API accepting only POST requests

In Task 01, I connected to OpenRouter and built a custom API using FastAPI. The service has a /chat endpoint that only accepts POST requests, sends the user prompt with the required headers and settings to the AI model, and returns the response while blocking any other HTTP methods with a 405 error.

### Task 02

#### Implement Conversational Memory

In Task 02, conversational memory is added to the FastAPI service to address the stateless nature of LLMs by locally retaining chat history and forwarding previous exchanges with every request. Rather than relying on provider-managed threads, Application-Managed Memory was chosen because it grants full control over context pruning, prevents vendor lock-in, avoids third-party storage fees, and aligns with standard AI engineering practices. For this implementation, the **Sliding Window** approach was utilized. The backend is configured to retain only the last 10 messages (exactly 5 user prompts and 5 AI responses) to efficiently manage the context window and optimize API costs.

### Task 03

#### Full-Stack Web Chatbot with Session & User Management

In Task 03, the chatbot is upgraded into a full-stack web application utilizing FastAPI, SQLite, and Tailwind CSS. The implementation focuses on secure chat isolation and a guest quota system that allows up to three free sessions before requiring authentication, seamlessly migrating this temporary history to the user's account upon login. Additionally, it features a modern UI equipped with sidebar session management (pin, rename, delete), full Markdown support, and custom Toast notifications for an optimized user experience.