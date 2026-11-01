# Task 02 — Conversational Memory

English | [فارسی](README_FA.md)

- **Duration**: 22 Sep 2026 – 28 Sep 2026
- **Files**: `app.py`, `chat_history.json`

### Implement Conversational Memory

The goal is to add conversational memory to the FastAPI service. Since LLMs are stateless, our API will store the message history locally and send previous messages with each request to preserve chat context.

There are two ways (comparison table):

| Feature | Application-Managed Memory | Provider-Managed Memory |
| :--- | :--- | :--- |
| **Token Cost** | Input tokens are identical, but you can prune history | Provider determines payload size |
| **Storage Fees** | Zero (stored in-memory or database) | Often billed per thread/vector store |
| **Control** | Full control over system prompts and context | Limited access inside provider black box |
| **Portability** | Universal; works across any provider or model | Locked into a single provider's API |
| **Implementation** | Requires writing custom state logic | Ready out of the box via thread IDs |

I chose Approach 1 (Application-Managed Memory) because it provides full control, eliminates vendor lock-in, and represents the industry standard in AI engineering.

To prevent token overflow and minimize API costs in production, the conversation history must be pruned rather than allowed to grow indefinitely. Two primary techniques can manage context size:

* **Sliding Window:** Retains only a fixed buffer of recent messages (e.g., the last 10 messages) while discarding older ones. While computationally cheap and simple to implement, its downside is that the model completely loses context from earlier turns.
* **Conversation Summarization:** Defines a threshold for message count. Once crossed, older turns are passed through the model to generate a concise summary. This summary is retained as a high-level system context alongside the latest turns, enabling long-term context retention while reducing input token usage.

For this implementation, I opted for the Sliding Window approach. The following configuration was added to the backend to retain only the last 10 messages (exactly 5 user prompts and 5 AI responses). This successfully manages the context window and marks the completion of Task 02:

```Python
WINDOW_SIZE = 10 # the last 5 prompts of user + 5 answer of ai = 10
```