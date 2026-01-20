import os
from dotenv import load_dotenv

load_dotenv()

# Google Trends
TRENDS_TIMEZONE = 360  # CST
TRENDS_HL = 'en-US'  # Host Language

# LLM (OpenRouter)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
GEMINI_MODEL = "xiaomi/mimo-v2-flash:free"
SITE_URL = "http://localhost:8501"
SITE_NAME = "Auto-Blog Pro"

# WordPress
WP_URL = os.getenv('WP_URL')
WP_USERNAME = os.getenv('WP_USERNAME')
WP_PASSWORD = os.getenv('WP_PASSWORD')  # Application Password

# Pexels (Image)
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
