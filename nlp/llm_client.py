
import os
from openai import OpenAI

client = OpenAI(api_key="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")



def get_gpt_response(history):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        max_tokens=100, 
        temperature=0.7,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. Keep your answers brief and to the point."            }
        ] + [
            {
                "role": msg["role"],
                "content": [{"type": "text", "text": msg["content"]}]
            } for msg in history
        ]
    )

    # Handle both new (list-based) and old (string) formats
    content = response.choices[0].message.content
    if isinstance(content, list):
        return content[0]["text"]
    return content  # it's already a plain string
