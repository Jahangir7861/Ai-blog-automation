import os
from auto_blog import config, trends, content, images
from wordpress_xmlrpc import Client

def test_connections():
    print("Testing Connections...")
    
    # Check Environment Variables
    missing_vars = []
    if not config.GEMINI_API_KEY: missing_vars.append("GEMINI_API_KEY")
    if not config.WP_URL: missing_vars.append("WP_URL")
    if not config.WP_USERNAME: missing_vars.append("WP_USERNAME")
    if not config.WP_PASSWORD: missing_vars.append("WP_PASSWORD")
    
    if missing_vars:
        print(f"ERROR: Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file.")
        return

    # 1. Test WordPress
    try:
        client = Client(config.WP_URL, config.WP_USERNAME, config.WP_PASSWORD)
        print("PASS: WordPress Connection (client initialized)")
    except Exception as e:
        print(f"FAIL: WordPress Connection - {e}")

    # 2. Test Google Trends
    try:
        kws = trends.get_trending_keywords("Test", limit=1)
        print("PASS: Google Trends Connectivity")
    except Exception as e:
        print(f"FAIL: Google Trends - {e}")

    # 3. Test Gemini
    try:
        import google.generativeai as genai
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        model.generate_content("hello")
        print("PASS: Gemini API")
    except Exception as e:
        print(f"FAIL: Gemini API - {e}")

    # 4. Test Pexels (Optional)
    if config.PEXELS_API_KEY:
        try:
            images.get_image_url("test")
            print("PASS: Pexels API")
        except Exception as e:
             print(f"FAIL: Pexels API - {e}")
    else:
        print("WARN: Pexels API Key missing (skipping)")

if __name__ == "__main__":
    test_connections()
