


#OLD ARTICLES WITH AI-GENERATED SUMMARY
# @login_required
# @views.route("/articles")
# def articles():
#     userpref = UserPreferences.query.filter_by(user_id=current_user.id).first()
#     #the articles which are shown change everytime this page is reloaded
#     article_list = []
#     news_list = []
#     ai_article_titles=['poop'] #To make sure chatgpt doesnt write repetitive articles.
#     blog_list = [] 
#     topic = session.get('ddoetopic')
#     topic_keywords = gpt.keywords(topic) 
#     print(topic_keywords)   
#     news_titles, news_urls = ddoecontent.fetch_news_articles(topic_keywords, 10)
#     blog_titles, blog_urls = ddoecontent.fetch_blog_articles(topic_keywords, 10)
#     for i in range(0, 10):
#         ai_article = gpt.ddoearticle(topic, userpref.age, ai_article_titles)
#         try:
#             summary = gpt.summary(ai_article[1])
#         except:
#             continue
#         ai_article_titles.append(ai_article[0])
#         article_list.append({'title': ai_article[0], 'text': ai_article[1], 'summary': summary})
#     for i in range(len(news_titles)): #Adding News Articles to 'article_list'
#         news_text, news_media = ddoecontent.scrape_articles(news_urls[i])
#         if news_text:
#             summary = gpt.summary(news_text[:500])
#         news_list.append({'title': news_titles[i], 'url': news_urls[i], 'text': news_text, 'media': news_media, 'summary': summary})
#         article_list.append({'title': news_titles[i], 'url': news_urls[i], 'text': news_text, 'media': news_media, 'summary': summary})
#     for i in range(len(blog_titles)): #Adding News Articles to 'article_list'
#         blog_text, blog_media = ddoecontent.scrape_articles(blog_urls[i])
#         if blog_text:
#             summary = gpt.summary(blog_text[:500])
#         blog_list.append({'title': blog_titles[i], 'url': blog_urls[i], 'text': blog_text, 'media': blog_media, 'summary': summary})
#         article_list.append({'title': blog_titles[i], 'url': blog_urls[i], 'text': blog_text, 'media': blog_media, 'summary': summary})
    
#     #MIGHT CHANGE IN THE FUTURE
#     random.shuffle(article_list)
#     print(len(article_list))
#     # show articles as a popup.
#     return render_template('articles.html', articles = article_list, news=news_list, blogs = blog_list)


