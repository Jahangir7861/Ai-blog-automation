from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost, GetPosts
from wordpress_xmlrpc.methods.media import UploadFile
from wordpress_xmlrpc.compat import xmlrpc_client
import mimetypes
import os
from .config import WP_URL, WP_USERNAME, WP_PASSWORD

def get_wp_client():
    return Client(WP_URL, WP_USERNAME, WP_PASSWORD)

def upload_image_to_wp(client, image_path, caption):
    """
    Uploads an image to the WordPress media library.
    """
    filename = os.path.basename(image_path)
    # guesses mime type
    mime_type = mimetypes.guess_type(filename)[0] or 'image/jpeg'
    
    data = {
        'name': filename,
        'type': mime_type,
    }
    
    with open(image_path, 'rb') as img:
        data['bits'] = xmlrpc_client.Binary(img.read())
        
    response = client.call(UploadFile(data))
    return {'id': response['id'], 'url': response.get('url', '')}

def create_wp_post(client, title, content, tags, image_id=None, categories=None, custom_fields=None):
    """
    Creates and publishes a new post on WordPress.
    custom_fields: list of dicts [{'key': '...', 'value': '...'}]
    """
    post = WordPressPost()
    post.title = title
    post.content = content
    post.terms_names = {
        'post_tag': tags.split(',') if tags else [],
        'category': categories if categories else ['Uncategorized']
    }
    
    if image_id:
        post.thumbnail = image_id
        
    if custom_fields:
        post.custom_fields = custom_fields
        
    post.post_status = 'publish' # or 'draft'
    
    post_id = client.call(NewPost(post))
    return post_id

def get_recent_posts(client, limit=10):
    """
    Fetches recent posts for internal linking.
    Returns list of dicts: [{'title': '...', 'link': '...'}]
    """
    try:
        posts = client.call(GetPosts({'number': limit, 'post_status': 'publish'}))
        results = []
        for p in posts:
            results.append({
                'title': p.title,
                'link': p.link
            })
        return results
    except Exception as e:
        print(f"Error fetching recent posts: {e}")
        return []

def get_all_posts(client):
    """
    Fetches ALL published posts (paginated) to build a full link index.
    """
    all_posts = []
    offset = 0
    batch_size = 20
    
    print("Fetching all posts for link index...")
    while True:
        try:
            posts = client.call(GetPosts({
                'number': batch_size, 
                'offset': offset, 
                'post_status': 'publish'
            }))
            
            if not posts:
                break
                
            for p in posts:
                all_posts.append({'title': p.title, 'link': p.link})
            
            offset += batch_size
            # Safety break to avoid infinite loops if API is weird
            if len(posts) < batch_size:
                break
        except Exception as e:
            print(f"Error fetching batch at offset {offset}: {e}")
            break
            
    print(f"Total posts fetched: {len(all_posts)}")
    return all_posts

if __name__ == "__main__":
    # Test connection
    client = get_wp_client()
    print("Connected to WordPress")
