import time
import os
from . import config, trends, content, images, wordpress

HISTORY_FILE = "posted_keywords.txt"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_history(keyword):
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{keyword}\n")

def run_automation_gen(sub_niche):
    """
    Generator function that yields status updates.
    """
    yield f"🚀 Starting automation for niche: {sub_niche}"
    
    # 1. Get Trending Keywords
    yield "🔍 Fetching trending keywords..."
    keywords = trends.get_trending_keywords(sub_niche)
    yield f"✅ Found keywords: {keywords}"
    
    if not keywords:
        yield "❌ No keywords found. Exiting."
        return

    posted_keywords = load_history()
    
    try:
        client = wordpress.get_wp_client()
        yield "✅ Connected to WordPress"
    except Exception as e:
        yield f"❌ WordPress Connection Failed: {e}"
        return

    for i, keyword in enumerate(keywords):
        if keyword in posted_keywords:
            yield f"⚠️ Skipping '{keyword}', already posted."
            continue
            
        yield f"⚙️ Processing keyword ({i+1}/{len(keywords)}): {keyword}"
        
        # 2. Generate Content
        yield "   📝 Generating blog post content..."
        post_data = content.generate_blog_post(keyword, sub_niche)
        if not post_data:
            yield "   ❌ Failed to generate content."
            continue
            
        yield f"   ✅ Generated title: {post_data['title']}"
        
        # 3. Get Image
        yield "   🖼️ Searching for image..."
        image_url = images.get_image_url(keyword)
        image_path = None
        image_id = None
        
        if image_url:
            yield f"   ⬇️ Downloading image..."
            image_path = images.download_image(image_url, f"temp_{keyword.replace(' ', '_')}.jpg")
            if image_path:
                yield "   ⬆️ Uploading image to WordPress..."
                try:
                    image_id = wordpress.upload_image_to_wp(client, image_path, keyword)
                    yield "   ✅ Image uploaded successfully."
                except Exception as e:
                    yield f"   ⚠️ Failed to upload image: {e}"
        else:
             yield "   ⚠️ No image found."
        
        # 4. Post to WordPress
        yield "   🚀 Publishing post..."
        try:
            post_id = wordpress.create_wp_post(
                client, 
                post_data['title'], 
                post_data['content'], 
                post_data['tags'], 
                image_id,
                categories=[sub_niche]
            )
            yield f"   🎉 Successfully published post ID: {post_id}"
            save_history(keyword)
        except Exception as e:
            yield f"   ❌ Failed to publish post: {e}"
            
        # Cleanup
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
            
        # Sleep to be nice to APIs
        yield "   💤 Waiting 5 seconds..."
        time.sleep(5)

    yield "🏁 Automation cycle complete."

if __name__ == "__main__":
    # CLI fallback
    niche = input("Enter sub-niche: ")
    for update in run_automation_gen(niche):
        print(update)
