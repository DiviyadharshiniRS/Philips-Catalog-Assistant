
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("NVIDIA_API_KEY")

if not api_key:
    raise ValueError("NVIDIA API key not found in .env")

try:
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
    )

    response = client.chat.completions.create(
        model="nvidia/nemotron-3.5-lightning-30b-a3b",
        messages=[
            {
                "role": "user",
                "content": "Explain Data Science in 2 simple sentences."
            }
        ],
        temperature=0.2,
        max_tokens=512,
        extra_body={
            "chat_template_kwargs": {
                "enable_thinking": False
            }
        }
    )

    answer = response.choices[0].message.content

    print("NVIDIA API connection successful!")
    print("\nAI Response:")
    print(answer if answer else "The API returned an empty response.")

except Exception as e:
    print("NVIDIA API request failed.")
    print("Error:", str(e))

finally:
    if "client" in locals():
        client.close()
