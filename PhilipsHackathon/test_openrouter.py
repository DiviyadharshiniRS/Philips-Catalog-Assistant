
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OpenRouter API key not found in .env")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

try:
    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: OpenRouter is working!"
            }
        ],
        max_tokens=1000,
        extra_body={
            "reasoning": {
                "effort": "low"
            }
        }
    )

    choice = response.choices[0]

    print("OpenRouter API connection successful!")
    print("Model used:", response.model)
    print("Finish reason:", choice.finish_reason)
    print("Token usage:", response.usage)

    answer = choice.message.content

    print("\nAI Response:")
    print(answer if answer else "No visible text returned.")

except Exception as e:
    print("OpenRouter API request failed.")
    print("Error:", str(e))

finally:
    client.close()
