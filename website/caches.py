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
    topic_key = f'articles:topic:{topic}:ids'
    
    cached_ids = cache.get(topic_key) or []
    cached_titles = {cache.get(f'articles:{id}:title') for id in cached_ids}

    
    for article in article_list:
        if article.get("title") not in cached_titles:
            unique_id = str(uuid.uuid4())
            
            cache_key = f'articles:{unique_id}'
            cache_data = {
                "topic": topic,
                "age": article.get("age"),
                "title": article.get("title"),
                "content": article.get("content"),
                "url": article.get("url"),
                "media": article.get("media")
            }
            
            cache.set(cache_key, cache_data)

            if unique_id not in cached_ids:
                cached_ids.append(unique_id)
    
    cache.set(topic_key, cached_ids)

    print("Articles cached successfully!")



def get_cached_articles(topic, min_count=10):
    topic_key = f'articles:topic:{topic}:ids'
    
    unique_ids = cache.get(topic_key) or []
    if not unique_ids:
        print("no articles cached for this topic, attempting to generate new ones")
    
    print(f"Retrieved article IDs for topic '{topic}': {unique_ids}")
    
    all_articles = []
    for unique_id in unique_ids:
        article = cache.get(f'articles:{unique_id}')
        if article:
            all_articles.append(article) 

    print(f"Found {len(all_articles)} articles in cache for topic '{topic}'.")

    while len(all_articles) < min_count:
        new_articles = find_articles(topic, length = min_count-len(all_articles))
        cache_articles(new_articles, topic)
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



def find_articles(topic, length=1):
    userpref = UserPreferences.query.filter_by(user_id=current_user.id).first()
    age = userpref.age if userpref else 17  
    
    article_list = []
    previous_ai_articles = []  
    topic_keywords = gpt.keywords(topic)
    
    news_titles, news_urls = ddoecontent.fetch_news_articles(topic_keywords, length)
    blog_titles, blog_urls = ddoecontent.fetch_blog_articles(topic_keywords, length)

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



def cache_youtube_shorts(reels, topic):
    cached_ids = cache.get(f'shorts:topic:{topic}:ids') or []
    for reel in reels:
        video_id = reel['video_id']
        if video_id not in cached_ids:
            cache_key = f'shorts:{video_id}'
            cache.set(cache_key, reel) 
            cached_ids.append(video_id)
            cache.set(f'shorts:topic:{topic}:ids', cached_ids)

    return {"message": f"{len(reels)} shorts cached successfully!", "new_cached_count": len(reels)}

def get_cached_shorts(topic, min_count=10):
    cached_ids_key = f'shorts:topic:{topic}:ids'
    cached_ids = cache.get(cached_ids_key) or []
    print(cached_ids)
    reels = [cache.get(f'shorts:{vid_id}') for vid_id in cached_ids if cache.get(f'shorts:{vid_id}')]

    if len(reels) < min_count:
        new_reels, _ = ddoecontent.fetch_youtube_shorts(query=topic, cached_ids=cached_ids, page_size=min_count - len(reels))
        
        if new_reels:
            cache_youtube_shorts(new_reels, topic)
            reels.extend(new_reels)

    return reels


#semi colons actually cannot be rearranged
def cache_topics(topic, age):
    cached_ids = cache.get(f'ddoetopic:age:{age}:ids') or []
    cached_topics = {cache.get(f'ddoetopic:{id}') for id in cached_ids if cache.get(f'ddoetopic:{id}')}
    
    if topic in cached_topics:
        return {"message": f"Topic '{topic}' already exists for age {age}.", "new_cached_count": 0}

    unique_id = str(uuid.uuid4())
    cache.set(f'ddoetopic:{unique_id}', topic)
    cached_ids.append(unique_id)
    cache.set(f'ddoetopic:age:{age}:ids', cached_ids)

    return {"message": f"{topic} topic cached successfully for age {age}!", "new_cached_count": 1}



def get_cached_topic(age, used_topics): #ammend used topics later
    cached_ids = cache.get(f'ddoetopic:age:{age}:ids') or []

    for unique_id in cached_ids:
        topic_list = cache.get(f'ddoetopic:{unique_id}')
        return random.choice(topic_list)

    new_topic = gpt.ddoetopic(current_user.id) 
    
    cache_topics(new_topic, age)
    
    return new_topic 



def cache_questions(topic, age, format, questionlist):
    cached_ids = cache.get(f'questions:topic:{topic}:format:{format}:ids') or []
    cached_questions = {cache.get(f'questions:{id}') for id in cached_ids if cache.get(f'questions:{id}')}
    for question in questionlist:
        if question in cached_questions:
            continue  
        unique_id = str(uuid.uuid4())
        cache.set(f'questions:{unique_id}', question)
        cached_ids.append(unique_id)

    cache.set(f'questions:topic:{topic}:format:{format}:ids', cached_ids)
    return {"message": f"questions finished caching"}


def get_cached_questions(topic, age, format):
    cache_key = f'questions:topic:{topic}:format:{format}:ids'
    cached_ids = cache.get(cache_key) or []
    questionlist = []
    if len(cached_ids) < 10:
        new_questions = gpt.create_test(topic, age, format, length=10 - len(cached_ids))
        cache_questions(topic, age, format, new_questions)
        cached_ids = cache.get(cache_key) or []

    for unique_id in cached_ids:
        question = cache.get(f'question:{unique_id}')
        if question:
            questionlist.append(question)

    return questionlist

    

def cache_words(word):
    cached_ids = cache.get(f'ddoeword:ids') or []
    cached_words = {cache.get(f'ddoeword:{id}') for id in cached_ids if cache.get(f'ddoeword:ids')}
    
    if word in cached_words:
        return {"message": f"Already exists"}

    unique_id = str(uuid.uuid4())
    cache.set(f'ddoeword:{unique_id}', word)
    cached_ids.append(unique_id)
    cache.set(f'ddoeword:ids', cached_ids)

    return {"message": f"successful"}

def get_cached_words():
    cache_key = f"ddoeword:ids"
    cached_ids = cache.get(cache_key) or []
    if len(cached_ids) == 0:
        new_word  = gpt.ddoeword()
        cache_words(new_word)
        return new_word
    else:
        word_id = random.choice(cached_ids)
        word = cache.get(f'ddoeword:{word_id}')
        return word




    
