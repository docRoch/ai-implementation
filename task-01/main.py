from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


client = OpenAI(
  base_url=OPENROUTER_URL,
  api_key=OPENROUTER_API_KEY
)

completion = client.chat.completions.create(
    extra_headers={
        "HTTP-Referer": "",
        "X-OpenRouter-Title": "",
    },
    model="~openai/gpt-sol-latest",
    max_tokens=300,
    messages=[
        {
            "role": "user",
            "content": "Explain AI in 5 words."
        }
    ]
)

print(completion.choices[0].message.content)

