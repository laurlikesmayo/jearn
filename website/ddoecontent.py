from newsapi import NewsApiClient
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import os
import yt_dlp
def configure():
    load_dotenv()
configure()
news_api = os.getenv('news_api')
google_api = os.getenv('google_api')
google_cse = os.getenv('google_cse')
tiktok_id = os.getenv('client_key')
tiktok_secret = os.getenv('client_secret')


def fetch_news_articles(query, page_size=25, exclude_domains=['removed.com', 'plos.org', 'youtube.com']):
    if isinstance(query, list):
        query = ' '.join(query)
    api_key = news_api  # Replace with your News API key
    url = f'https://newsapi.org/v2/everything?q={query}&pageSize={page_size}&apiKey={api_key}'
    response = requests.get(url)
    articles = response.json().get('articles', [])

    filtered_articles = [(article['title'], article['url']) for article in articles
                         if not any(domain in article['url'] for domain in exclude_domains)]

    if not filtered_articles:
        return [], []  # Return empty lists if no articles match the criteria

    all_titles, all_urls = zip(*filtered_articles)  # Unzip titles and URLs from filtered articles

    return all_titles, all_urls

def fetch_blog_articles(query, page_size=25, exclude_domains=['removed.com', 'plos.org', 'youtube.com']):
    if isinstance(query, list):
        query = ' '.join(query)
    api_key=google_api
    cse_id=google_cse
    # api_key = 'AIzaSyAjSqLZie3RmSvPt4Xz4fv5yshxk0SFmx8' #remember to comment this out
    # cse_id = '16a4cc97a3b434de8' #remember to comment this out
    url = f'https://www.googleapis.com/customsearch/v1?q={query}&cx={cse_id}&key={api_key}&num={page_size}'
    response = requests.get(url)
    search_results = response.json().get('items', [])

    filtered_articles = [(article['title'], article['link']) for article in search_results
                         if not any(domain in article['link'] for domain in exclude_domains)]

    if not filtered_articles:
        return [], []  # Return empty lists if no articles match the criteria

    all_titles, all_urls = zip(*filtered_articles)  # Unzip titles and URLs from filtered articles

    return all_titles, all_urls

import requests


def fetch_youtube_shorts(query, cached_ids=None, page_size=10, duration='short', page_token=None):
    all_reels = []
    api_key = google_api  # Replace with your API key
    search_url = 'https://www.googleapis.com/youtube/v3/search'
    video_details_url = 'https://www.googleapis.com/youtube/v3/videos'

    # Search parameters
    search_params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'videoDuration': duration,
        'maxResults': page_size,
        'key': api_key
    }

    if page_token:
        search_params['pageToken'] = page_token

    response = requests.get(search_url, params=search_params)
    
    if response.status_code == 200:
        results = response.json()
        video_ids = [item['id']['videoId'] for item in results['items'] if item['id']['videoId'] not in cached_ids]

        # Get video details to filter out unavailable videos
        video_params = {
            'part': 'status',
            'id': ','.join(video_ids),
            'key': api_key
        }
        video_response = requests.get(video_details_url, params=video_params)
        
        if video_response.status_code == 200:
            video_results = video_response.json()
            for item in video_results['items']:
                video_id = item['id']
                
                # Check if the video is public and embeddable
                if item['status']['privacyStatus'] == 'public' and item['status'].get('embeddable', False):
                    title = next((video['snippet']['title'] for video in results['items'] if video['id']['videoId'] == video_id), 'Unknown Title')
                    all_reels.append({'title': title, 'url': f'https://www.youtube.com/watch?v={video_id}', 'video_id': video_id})

        # Return reels and the next page token for further fetching if needed
        next_page_token = results.get('nextPageToken')
        return all_reels, next_page_token
    else:
        print(f"Error: {response.status_code}")
        return [], None



    
def fetch_tiktok(query, page_size=25): #must fix
    client_id = tiktok_id
    client_secret = tiktok_secret
    if isinstance(query, list):
        query = ' '.join(query)
    # Step 1: Get access token using OAuth 2.0
    auth_url = 'https://openapi.tiktok.com/oauth/access_token'
    auth_data = {
        'client_key': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    auth_response = requests.post(auth_url, data=auth_data)
    auth_data = auth_response.json()

    access_token = auth_data.get('access_token')

    # Step 2: Search for videos related to a topic
    search_url = 'https://api.tiktok.com/api/item_list/'
    params = {
        'count': page_size,  # Number of videos to retrieve
        'keyword': query,
        'access_token': access_token
    }

    response = requests.get(search_url, params=params)
    videos = response.json()
    all_urls = [video['video']['downloadAddr'] for video in videos.get('items', [])]
    all_titles = [video['desc'] for video in videos.get('items', [])]
    return all_titles, all_urls
    
def scrape_articles(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f'Failed to retrieve page: {response.status_code}')
        return "", []  # Ensure it returns an empty string and an empty list

    soup = BeautifulSoup(response.content, 'html.parser')
    article_text = ''
    article_media = []

    # Extract text content
    for tag in ['article', 'div', 'main']:
        content = soup.find_all(tag)
        for section in content:
            paragraphs = section.find_all('p')
            if paragraphs:
                article_text += ' '.join([para.get_text() for para in paragraphs])

    # Extract media content
    media_tags = ['video', 'img', 'iframe', 'embed', 'audio', 'source']
    for tag in media_tags:
        for media in soup.find_all(tag):
            src = media.get('src')
            if src:
                article_media.append(src)
            # Check for nested sources in picture tags
            if tag == 'picture':
                sources = media.find_all('source')
                for source in sources:
                    src = source.get('src')
                    if src:
                        article_media.append(src)

    return article_text, article_media


def is_embeddable(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return False
        soup = BeautifulSoup(response.text, 'html.parser')
        # Check for X-Frame-Options or Content-Security-Policy headers
        x_frame_options = response.headers.get('X-Frame-Options')
        csp = response.headers.get('Content-Security-Policy')
        if x_frame_options and x_frame_options.lower() in ['deny', 'sameorigin']:
            return False
        if csp and 'frame-ancestors' in csp:
            return False
        return True
    except:
        return False

import yt_dlp

# def get_video_info(id): #slow method
#     url = f'https://www.youtube.com/watch?v={id}'
#     ydl_opts = {
#         'quiet': True,  # Suppress output
#         'noplaylist': True,  # Only process the single video, not playlists
#         'skip_download': True,  # Skip downloading the video
#         'extract_flat': True,  # Only extract the flat metadata (avoids unnecessary details)
#         'writeinfojson': False,  # Do not write metadata to a JSON file
#     }
    
#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info = ydl.extract_info(url, download=False)
        
#     width = info.get('width')
#     height = info.get('height')
    
#     if width is None or height is None:
#         raise Exception("Unable to get video dimensions")
    
#     return height, width

def get_video_info(video_id):
    url = f'https://www.youtube.com/watch?v={video_id}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find dimensions in the page source
    # Note: This approach may vary depending on YouTube's page structure
    meta_tags = soup.find_all('meta')
    for tag in meta_tags:
        if 'property' in tag.attrs and tag.attrs['property'] == 'og:video:width':
            width = tag.attrs['content']
        elif 'property' in tag.attrs and tag.attrs['property'] == 'og:video:height':
            height = tag.attrs['content']
    
    return width, height





# topics = ['AI']
# titles, sources, urls= fetch_news_articles(topics)

#print(scrape_articles('https://en.wikipedia.org/wiki/Natalia_Grossman'))

# testing

# for i in range(len(titles)):
#     print(len(titles))
#     print(f"Article {i + 1}:")
#     print(f"Title: {titles[i]}")
#     print(f"Source: {sources[i]}")
#     print(f"URL: {urls[i]}")
#     print("-" * 50)

#     print(scrape_articles(urls[i]))

# news, urls = fetch_news_articles('coding', 10)
# print(scrape_articles(urls[0]))
