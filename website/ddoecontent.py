from newsapi import NewsApiClient
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import os
def configure():
    load_dotenv()
configure()
news_api = os.getenv('news_api')
google_api = os.getenv('googlejson_api')
google_cse = os.getenv('googjson_cse')
tiktok_id = os.getenv('client_key')
tiktok_secret = os.getenv('client_secret')


def fetch_news_articles(query, page_size=25, exclude_domains=['removed.com', 'plos.org']):
    if isinstance(query, list):
        query = ' '.join(query)
    api_key = 'your_news_api_key'  # Replace with your News API key
    url = f'https://newsapi.org/v2/everything?q={query}&pageSize={page_size}&apiKey={api_key}'
    response = requests.get(url)
    articles = response.json().get('articles', [])

    filtered_articles = [(article['title'], article['url']) for article in articles
                         if not any(domain in article['url'] for domain in exclude_domains)]

    if not filtered_articles:
        return [], []  # Return empty lists if no articles match the criteria

    all_titles, all_urls = zip(*filtered_articles)  # Unzip titles and URLs from filtered articles

    return all_titles, all_urls

def fetch_blog_articles(query, page_size=25, exclude_domains=['removed.com', 'plos.org']):
    if isinstance(query, list):
        query = ' '.join(query)
    api_key = 'your_google_api_key'  # Replace with your Google API key
    cse_id = 'your_google_cse_id'  # Replace with your Google CSE ID
    url = f'https://www.googleapis.com/customsearch/v1?q={query}&cx={cse_id}&key={api_key}&num={page_size}'
    response = requests.get(url)
    search_results = response.json().get('items', [])

    filtered_articles = [(article['title'], article['link']) for article in search_results
                         if not any(domain in article['link'] for domain in exclude_domains)]

    if not filtered_articles:
        return [], []  # Return empty lists if no articles match the criteria

    all_titles, all_urls = zip(*filtered_articles)  # Unzip titles and URLs from filtered articles

    return all_titles, all_urls

def fetch_tiktok(query, page_size=25):
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

#print(fetch_blog_articles('coding', 10))