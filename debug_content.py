from auto_blog import content, config
import google.generativeai as genai

# Reload config to be sure
import os
from dotenv import load_dotenv
load_dotenv("auto_blog/.env")
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

print(f"Using Model: {config.GEMINI_MODEL}")

print("Testing generation...")
res = content.generate_blog_post("Test Keyword", "General")
if res:
    print("SUCCESS")
    print(res['title'])
else:
    print("FAILED")
