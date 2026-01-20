import requests
import json
import time
import random
from .config import OPENROUTER_API_KEY, GEMINI_MODEL, SITE_URL, SITE_NAME

def retry_with_backoff(func):
    """
    Decorator to handle rate limits (429) and server errors.
    """
    def wrapper(*args, **kwargs):
        attempts = 0
        max_attempts = 5
        delay = 10 
        
        while attempts < max_attempts:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "500" in error_str or "502" in error_str:
                    print(f"API Error ({error_str}). Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2 
                    attempts += 1
                else:
                    raise e
        print("Max retries exceeded.")
        return None
    return wrapper

@retry_with_backoff
def query_llm(prompt, reasoning_enabled=False):
    """
    Sends a prompt to OpenRouter and returns the text response.
    Supports reasoning if enabled.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": SITE_URL, 
        "X-Title": SITE_NAME, 
    }
    data = {
        "model": GEMINI_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    if reasoning_enabled:
        data["reasoning"] = {"enabled": True}
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code != 200:
        raise Exception(f"OpenRouter Error {response.status_code}: {response.text}")
        
    json_response = response.json()
    if 'choices' in json_response and len(json_response['choices']) > 0:
        return json_response['choices'][0]['message']['content']
    else:
        return ""

def generate_titles(keyword, count=5):
    """
    Generates a list of catchy blog titles for a keyword.
    Enforces INFORMATIONAL framing (How-to, Guides, etc.).
    """
    prompt = f"""
    Generate {count} catchy, SEO-friendly, and viral blog post titles for the keyword: "{keyword}".
    
    IMPORTANT: Format these as INFORMATIONAL content (e.g., "How to...", "Ultimate Guide to...", "X Tips for...", "Why you should..."). 
    Avoid purely commercial titles (like "Buy X" or "X Service").
    
    Return ONLY the titles, one per line. No numbers or bullets.
    """
    text = query_llm(prompt)
    if not text: return []
    return [line.strip() for line in text.split('\n') if line.strip()]

def generate_blog_post(topic, sub_niche, internal_links=None):
    """
    Generates a blog post using OpenRouter with strict validation rules.
    internal_links: list of dicts [{'title': '...', 'link': '...'}]
    """
    
    links_prompt = ""
    if internal_links:
        links_prompt = "\n\nReferenced Internal Content (Include natural links to these if relevant):\n"
        for item in internal_links:
            links_prompt += f"- {item['title']}: {item['link']}\n"
    
    prompt = f"""
    You are a professional blog writer.
    Write a high-quality, SEO-optimized blog post with the title: "{topic}".
    The blog is focused on the niche: "{sub_niche}".
    {links_prompt}

    STRICT VALIDATION RULES (MUST FOLLOW ALL):
    1. Word Count: Must be 1500+ words. If short, expand sections, add H2s, add FAQ, add examples.
    2. Originality: Rewrite from scratch, no plagiarism.
    3. Human Tone: No robotic/repetitive language. Use short/mixed sentences and natural transitions.
    4. Search Intent: Answer the topic directly in first 150 words.
    5. Structure: Proper Intro (100-150 words), H2/H3 headings, short paragraphs, bullets.
    6. Value: Remove filler. Add explanations, comparisons, and examples per paragraph.
    7. User Help: Add step-by-step instructions, real-life examples, tips.
    8. Safety: NO restricted topics (adult, gambling, etc.). Refuse if unsafe.
    9. Disclaimer: Add medical/financial disclaimer if applicable.
    10. Keywords: No stuffing. Use synonyms and natural flow.
    11. FAQ: MANDATORY. Add 3–6 relevant FAQs with clear answers.
    12. Intro: 100+ words, state problem, explain what reader will learn.
    13. Conclusion: Summary + key points.
    14. Final Check: If any rule fails, FIX IT before outputting.
    15. Internal Linking: If provided, naturally weave the 'Referenced Internal Content' links into the text where they fit. Do not force them.
    16. Meta Data: Generate an SEO-optimized Meta Title (max 60 chars) and Meta Description (max 160 chars).

    Structure the response in the following format exactly, do not add any markdown code blocks around the whole response, just raw text with separators:
    
    TITLE: <Use the provided title>
    META TITLE: <SEO optimized title>
    META DESCRIPTION: <SEO optimized description>
    CONTENT:
    <Insert blog content here in HTML format. Use <h2> for headings, <p> for paragraphs, <ul>/<li> for lists. Do not use <h1>.>
    TAGS: <Insert comma separated tags>
    excerpt: <Insert a short excerpt for the post>
    """
    
    # Enable reasoning for complex content generation
    text = query_llm(prompt, reasoning_enabled=True)
    if not text: return None
    
    # Parse the response
    title = ""
    meta_title = ""
    meta_desc = ""
    content_body = ""
    tags = ""
    excerpt = ""
    
    lines = text.split('\n')
    current_section = None
    
    for line in lines:
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
        elif line.startswith("META TITLE:"):
            meta_title = line.replace("META TITLE:", "").strip()
        elif line.startswith("META DESCRIPTION:"):
            meta_desc = line.replace("META DESCRIPTION:", "").strip()
        elif line.startswith("CONTENT:"):
            current_section = "CONTENT"
        elif line.startswith("TAGS:"):
            current_section = None
            tags = line.replace("TAGS:", "").strip()
        elif line.startswith("excerpt:"):
            current_section = None
            excerpt = line.replace("excerpt:", "").strip()
        elif current_section == "CONTENT":
            content_body += line + "\n"
    
    if not title: title = topic # Fallback
    
    return {
        "title": title,
        "meta_title": meta_title,
        "meta_desc": meta_desc,
        "content": content_body.strip(),
        "tags": tags,
        "excerpt": excerpt
    }

def validate_post_structure(post_data):
    """
    Deterministically validates the strict rules.
    Returns a list of (Check Name, Passed/Failed Boolean, Details)
    """
    content = post_data.get('content', '')
    word_count = len(content.split())
    
    checks = []
    
    # 1. Word Count > 1500
    if word_count >= 1500:
        checks.append(("Word Count > 1500", True, f"Count: {word_count}"))
    else:
        checks.append(("Word Count > 1500", False, f"Count: {word_count} (Too short!)"))
        
    # 2. FAQ Section (Simple heuristic: look for "FAQ" or "Frequently Asked Questions" headers)
    if "FAQ" in content or "Frequently Asked Questions" in content or "?" in content:
         checks.append(("FAQ Section", True, "Detected question marks/headers"))
    else:
         checks.append(("FAQ Section", False, "No FAQ section found"))
         
    # 3. Headings (H2)
    if "<h2>" in content:
        checks.append(("Heading Structure", True, "H2 tags found"))
    else:
        checks.append(("Heading Structure", False, "No H2 tags found"))
        
    # 4. Lists
    if "<ul>" in content or "<ol>" in content or "<li>" in content:
         checks.append(("Formatting", True, "Lists detected"))
    else:
         checks.append(("Formatting", False, "No list formatting found"))
         
    return checks

if __name__ == "__main__":
    print(generate_titles("Test Keyword"))
