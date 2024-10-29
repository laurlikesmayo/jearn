import json
import uuid
from flask import jsonify
from . import gpt, ddoecontent, cache

def cache_articles(topic, age, previous_article_titles = ""):
    #Add a code about retrieving / storing the previous article titles
    article = gpt.ddoearticle(topic, age, previous_article_titles)
    unique_id = str(uuid.uuid4())
    title = article["title"]
    content = article["content"]
    cache_key = f'articles:{unique_id}'
    cache.set(cache_key, {
        "topic": topic,
        "age": age,
        "title": title,
        "content": content
    })

    #The topic cache maintains a list of unique IDs associated with each topic. This allows you to retrieve all articles under a specific topic easily.
    topic_key = f'articles:topic:{topic}'
    cached_ids = cache.get(topic_key) or []
    if unique_id not in cached_ids:
        cached_ids.append(unique_id)
        cache.set(topic_key, cached_ids)

    return jsonify({"message": "Article cached successfully!", "id": unique_id}), 201

def articles_from_cache(topic):
    topic_key = f'articles:topic:{topic}'
    unique_ids = cache.get(topic_key)
    
    if not unique_ids:
        #Add code about having to generate from API key, or go back to fetch_articles function
        return jsonify({"message": "No articles found for this topic."}), 404
    
    articles = []
    for unique_id in unique_ids:
        article = cache.get(f'articles:{unique_id}')
        if article:
            articles.append(article)
    
    return jsonify(articles), 200