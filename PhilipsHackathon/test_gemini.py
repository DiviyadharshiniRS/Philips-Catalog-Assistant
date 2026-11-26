
import os
from dotenv import load_dotenv
from google import genai

# Load API key from .env
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("Google API key not found in .env")

# Initialize Gemini client
client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents="Explain Data Science in 2 simple sentences."
    )

    print("Gemini API connection successful!")
    print("\nAI Response:")
    print(response.text)

except Exception as e:
    print("Gemini API request failed.")
    print("Error:", str(e))

finally:
    client.close()
