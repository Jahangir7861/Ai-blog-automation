import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv("auto_blog/.env")
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

candidates = [
    "gemini-1.5-flash",
    "models/gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "models/gemini-1.5-flash-001",
    "gemini-pro",
    "models/gemini-pro",
    "gemini-1.5-pro",
    "gemini-1.5-flash-latest"
]

print("Testing candidates...")
for model_name in candidates:
    print(f"Trying: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello")
        print(f"SUCCESS with {model_name}")
        break 
    except Exception as e:
        print(f"FAILED with {model_name}: {e}")
