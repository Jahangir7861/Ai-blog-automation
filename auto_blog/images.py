import requests
import random
from .config import PEXELS_API_KEY

def get_images(query, count=1):
    """
    Searches Pexels and returns a list of image URLs.
    """
    if not PEXELS_API_KEY:
        print("Pexels API Key is missing.")
        return []

    url = "https://api.pexels.com/v1/search"
    headers = {
        "Authorization": PEXELS_API_KEY
    }
    # Request more than needed to ensure uniqueness/randomness
    per_page = max(5, count * 2)
    params = {
        "query": query,
        "per_page": per_page,
        "orientation": "landscape"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data['photos']:
            # Shuffle and pick 'count' unique photos
            photos = data['photos']
            random.shuffle(photos)
            
            urls = []
            for p in photos[:count]:
                urls.append(p['src']['original']) # or 'large'
            return urls
        else:
            print(f"No images found for {query}")
            return []

    except Exception as e:
        print(f"Error fetching images for {query}: {e}")
        return []

# Backwards compatibility alias
def get_image_url(query):
    imgs = get_images(query, count=1)
    return imgs[0] if imgs else None

def download_image(url, filename="temp_image.jpg"):
    """
    Downloads the image from the URL and saves it locally.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                 out_file.write(chunk)
        return filename
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

if __name__ == "__main__":
    url = get_image_url("Vegan Food")
    print("Image URL:", url)
    if url:
        download_image(url)
