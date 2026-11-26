
import os
from dotenv import load_dotenv
from groq import Groq

# Load API key
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("Groq API key not found in .env")

# Connect to Groq
client = Groq(api_key=api_key)

try:
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": "Explain Data Science in 2 simple sentences."
            }
        ],
        max_completion_tokens=150
    )

    print("Groq API connection successful!")
    print("\nAI Response:")
    print(response.choices[0].message.content)

except Exception as e:
    print("Groq API request failed.")
    print("Error:", str(e))
