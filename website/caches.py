import json
import uuid
from . import app, db, cache
from .models import Users, UserPreferences, DDOE
from flask import jsonify
from . import gpt, ddoecontent
from flask_login import current_user
import random
import uuid
from dotenv import load_dotenv
import os

'''
IMPORTANT NOTE 
THERE ARE MANY FACTORS I DID NOT TAKE INTO ACCOUNT WHICH CAN AFFECT USER EXPERIENCE

- TRACKING ARTICLES THAT THE USER HAS ALREADY SEEN
- TOPIC SPECIFIC CACHING GROWTH - TOO MANY ARTICLES UNDER THE SAME TOPIC CAN AFFECT MEMORY AND SPEED
    - Set cache to only store the 'latest 50 articles'
    - Set cache articles to have an expiration date
    - Manual clearing of expired articles
- FETCH CACHED ARTICLES BASED ON TOPIC AND AGE

'''

def cache_articles(article_list, topic):
    # Prepare the topic-specific cache list key
    topic_key = f'articles:topic:{topic}:ids'
    
    # Fetch existing article IDs from the cache or create a new list
    cached_ids = cache.get(topic_key) or []
    cached_titles = {cache.get(f'articles:{id}:title') for id in cached_ids}

    
    for article in article_list:
        if article.get("title") not in cached_titles:
            unique_id = str(uuid.uuid4())
            
            # Prepare cache key for the article and structure data
            cache_key = f'articles:{unique_id}'
            cache_data = {
                "topic": topic,
                "age": article.get("age"),
                "title": article.get("title"),
                "content": article.get("content"),
                "url": article.get("url"),
                "media": article.get("media")
            }
            
            # Store the individual article in the cache
            cache.set(cache_key, cache_data)

            # Update the topic-specific cache list with this unique ID
            if unique_id not in cached_ids:
                cached_ids.append(unique_id)
    
    # Store the updated list of article IDs back to the cache
    cache.set(topic_key, cached_ids)

    print("Articles cached successfully!")



def get_cached_articles(topic, min_count=10):
    # Key for topic-specific articles list
    topic_key = f'articles:topic:{topic}:ids'
    
    # Retrieve the list of article IDs from the cache
    unique_ids = cache.get(topic_key) or []
    if not unique_ids:
        print("no articles cached for this topic, attempting to generate new ones")
    
    print(f"Retrieved article IDs for topic '{topic}': {unique_ids}")
    
    # Retrieve cached articles based on stored IDs
    all_articles = []
    for unique_id in unique_ids:
        article = cache.get(f'articles:{unique_id}')
        if article:
            all_articles.append(article)  # Add the article to the list

    print(f"Found {len(all_articles)} articles in cache for topic '{topic}'.")
    # If we don't have enough cached articles, generate more and cache them

    while len(all_articles) < min_count:
        # Fetch/generate new articles for the topic
        new_articles = find_articles(topic, length = min_count-len(all_articles))
        # Cache the new articles
        cache_articles(new_articles, topic)
        # Update the list of all articles to include the new ones
        all_articles.extend(new_articles)

    return all_articles

def cache_questions(question, topic):
    unique_id = str(uuid.uuid4())
    print(unique_id)
    cache_key = f'question:{unique_id}'
    cache_data = {
        "topic": topic,
        "question": question
    }



#Generates/Scrapes 5 articles
def find_articles(topic, length=1):
    userpref = UserPreferences.query.filter_by(user_id=current_user.id).first()
    age = userpref.age if userpref else 17  # Default age if no user preference is found
    
    article_list = []
    previous_ai_articles = []  # Prevent duplicate AI-generated titles
    topic_keywords = gpt.keywords(topic)
    
    # Fetch news and blog article details based on topic keywords
    news_titles, news_urls = ddoecontent.fetch_news_articles(topic_keywords, length)
    blog_titles, blog_urls = ddoecontent.fetch_blog_articles(topic_keywords, length)

    # Generate AI articles
    for _ in range(length):
        ai_article = gpt.ddoearticle(topic, age, previous_ai_articles)
        if 'title' in ai_article and 'content' in ai_article:
            previous_ai_articles.append(ai_article["title"])
            article_list.append({
                "title": ai_article["title"],
                "content": ai_article["content"],
                "topic": topic,
                "age": age
            })

    # Adding News Articles
    try:
        for i in range(len(news_titles)):
            if ddoecontent.is_embeddable(news_urls[i]):
                news_text, news_media = ddoecontent.scrape_articles(news_urls[i])
                article_list.append({
                    'title': news_titles[i],
                    'url': news_urls[i],
                    'content': news_text,
                    'media': news_media,
                    'topic': topic,
                    'age': age
                })
    except Exception as e:
        print(f"Error fetching news articles: {e}")

    # Adding Blog Articles
    try:
        for i in range(len(blog_titles)):
            if ddoecontent.is_embeddable(blog_urls[i]):
                blog_text, blog_media = ddoecontent.scrape_articles(blog_urls[i])
                article_list.append({
                    'title': blog_titles[i],
                    'url': blog_urls[i],
                    'content': blog_text,
                    'media': blog_media,
                    'topic': topic,
                    'age': age
                })
    except Exception as e:
        print(f"Error fetching blog articles: {e}")

    # Optional: randomize order for varied display
    # random.shuffle(article_list)

    return article_list


#REELS

def cache_youtube_shorts(reels, topic):
    cached_ids = cache.get(f'shorts:topic:{topic}:ids') or []
    for reel in reels:
        video_id = reel['video_id']
        # Cache each unique reel individually
        if video_id not in cached_ids:
            cache_key = f'shorts:{video_id}'
            cache.set(cache_key, reel)  # Store the reel
            
            # Update topic-specific ID list
            cached_ids.append(video_id)
            cache.set(f'shorts:topic:{topic}:ids', cached_ids)

    return {"message": f"{len(reels)} shorts cached successfully!", "new_cached_count": len(reels)}

def get_cached_shorts(topic, min_count=10):
    cached_ids_key = f'shorts:topic:{topic}:ids'
    cached_ids = cache.get(cached_ids_key) or []
    print(cached_ids)
    reels = [cache.get(f'shorts:{vid_id}') for vid_id in cached_ids if cache.get(f'shorts:{vid_id}')]

    # Check if we have enough cached reels; fetch more if needed
    if len(reels) < min_count:
        new_reels, _ = ddoecontent.fetch_youtube_shorts(query=topic, cached_ids=cached_ids, page_size=min_count - len(reels))
        
        if new_reels:
            cache_youtube_shorts(new_reels, topic)
            reels.extend(new_reels)

    return reels



def cache_topics(topic, age):
    # Create a cache key based on the topic and age
    cache_key = f'topics:{topic}:age:{age}'
    
    # Check if the topic already exists for the specified age
    if cache.get(cache_key):
        return {"message": f"The topic '{topic}' for age {age} already exists in the cache."}
    
    # Store the topic with a unique ID
    unique_id = str(uuid.uuid4())  # Generate a unique ID for this entry
    cache.set(cache_key, unique_id)  # Store the unique ID for the topic and age
    
    # Update the list of cached IDs for this age group

    #searches for cached id's based on the age.
    cached_ids = cache.get(f'topics:age:{age}:ids') or []
    cached_ids.append(unique_id)
    cache.set(f'topics:age:{age}:ids', cached_ids)

    return {"message": f"{topic} topic cached successfully for age {age}!", "new_cached_count": 1}

def get_cached_topic(age, used_topics):
    # Get the list of cached IDs for the specified age
    cached_ids = cache.get(f'topics:age:{age}:ids') or []

    # Retrieve cached topics based on IDs
    for unique_id in cached_ids:
        topic = cache.get(f'topics:{unique_id}')  # Get the topic based on the unique ID
        if topic and topic not in used_topics:
            return topic  # Return the first new topic found

    # If no new cached topic exists, fetch a new topic using gpt.ddoetopics
    new_topic = gpt.ddoetopic(current_user.id)  # Adjust this function call as needed
    
    # Optionally cache the new topic
    cache_topics(new_topic, age)  # Cache the new topic for the specified age
    
    return new_topic  # Return the newly generated topic
