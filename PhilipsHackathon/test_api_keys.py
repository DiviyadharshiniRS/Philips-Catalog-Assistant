import os
from dotenv import load_dotenv

load_dotenv()

providers = {
    "Groq": "GROQ_API_KEY",
    "Google": "GOOGLE_API_KEY",
    "NVIDIA": "NVIDIA_API_KEY",
    "OpenRouter": "OPENROUTER_API_KEY"
}

for provider, variable in providers.items():
    status = bool(os.getenv(variable))
    print(f"{provider}: {'Loaded' if status else 'Missing'}")