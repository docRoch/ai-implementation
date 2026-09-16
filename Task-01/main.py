from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
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

