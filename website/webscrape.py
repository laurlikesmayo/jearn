from newsapi import NewsApiClient
from dotenv import load_dotenv
import os
# def configure():
#     load_dotenv()
# configure()
#api_key = os.getenv('news_api')

api_key = '1ccda668338e4ca999cd7340756a0c78'  # Replace with your actual NewsAPI key
newsapi = NewsApiClient(api_key=api_key)

def fetch_news_articles(topics, language='en', page_size=5):
    """
    Fetches top headlines for each topic provided.

    Args:
    - topics (list): List of topics or keywords to search for.
    - language (str, optional): Language code for the articles. Defaults to 'en'.
    - page_size (int, optional): Number of articles to fetch per topic. Defaults to 5.

    Returns:
    - tuple: Three lists (titles, sources, urls) containing the fetched article details.
    """
    all_titles = []
    all_sources = []
    all_urls = []

    for topic in topics:
        print(f"Fetching top headlines for '{topic}':")
        top_headlines = newsapi.get_top_headlines(q=topic, language=language, page_size=page_size)

        # Process the results
        if top_headlines['status'] == 'ok':
            articles = top_headlines['articles']
            for article in articles:
                all_titles.append(article['title'])
                all_sources.append(article['source']['name'])
                all_urls.append(article['url'])
        else:
            print(f"Failed to fetch top headlines for '{topic}':", top_headlines['message'])

    return all_titles, all_sources, all_urls
    
def scrape_articles(title, source, url):
    #work on this later
    return 0

