## Task 02

- Duration:
    - Start: 22 Sep 2026
    - End: In Progress

- Files:
    - app.py

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