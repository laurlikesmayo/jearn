@app.route('/load-articles', methods=['GET'])
def load_articles():
    topic = request.args.get('topic')
    offset = int(request.args.get('offset', 0))
    articles = fetch_next(topic, offset)  # Fetch next articles based on offset
    return jsonify(articles)

def fetch_next(topic, offset=0, decide = random.choice([True, False])):
    userpref = UserPreferences.query.filter_by(user_id=current_user.id).first()
    article_list = []
    ai_article_titles = ['poop']  # Ensure unique titles for GPT-generated articles
    
    # Get keywords from the topic
    topic_keywords = gpt.keywords(topic)
    print(topic_keywords)

    # Fetch blog articles
    # Fetch blog articles and ensure we convert the returned tuple to lists
    blog_titles, blog_urls = ddoecontent.fetch_blog_articles(topic_keywords, 1)  # Fetch 2 blog articles
    blog_titles = list(blog_titles)  # Convert tuple to list
    blog_urls = list(blog_urls)      # Convert tuple to list

    # Randomly decide to either fetch a blog article or generate an AI article
    if decide and blog_titles and ddoecontent.is_embeddable(blog_urls[0]):
        blog_text, blog_media = ddoecontent.scrape_articles(blog_urls[0])
        article_list.append({
            'title': blog_titles[0],
            'url': blog_urls[0],
            'text': blog_text,
            'media': blog_media
        })
        blog_titles.pop(0)  # Remove the title and URL that was used
        blog_urls.pop(0)

    else:
        # Generate an AI article
        ai_article = gpt.ddoearticle(topic, userpref.age, ai_article_titles)
        try:
            if ai_article[1] is not None and len(ai_article[1]) >= 25:
                ai_article_titles.append(ai_article[0])
                article_list.append({'title': ai_article[0], 'text': ai_article[1]})
        except Exception as e:
            print(f"Error generating AI article: {e}")

    # Return the articles based on the offset
    return article_list[offset:offset + 1]