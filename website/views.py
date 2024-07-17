from flask import Flask, Blueprint, render_template, request, url_for, redirect, session, flash, jsonify
from datetime import timedelta, datetime
from werkzeug.security import generate_password_hash, check_password_hash 
from .models import Users, UserPreferences, DDOE
import random
from flask_login import login_user, logout_user, login_required, UserMixin, current_user
from . import gpt, ddoecontent
import json

from . import app, db
views = Blueprint("views", __name__)

@app.before_request
def before_request_func():
    if not current_user:
        return redirect(url_for('views.login'))

@views.route('/login',  methods=['GET', 'POST'] )
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        permanentsesh = request.form.get('permanentsession') == 'true' #returns bool
        user = Users.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=permanentsesh)
                print('Logged in')
                flash('Log in sucessful', 'info ')
                return redirect(url_for('views.home')) 
            else:
                flash('Wrong Password')
        else:
            flash('Username does not exist')
                
                
    return render_template("login.html")

@views.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if not username or not password1:
            flash("Username or password cannot be empty!")
        elif len(password1) < 6 or len(username) < 6:
            flash("Username and password must contain at least 6 characters!")
        elif password1 != password2:
            flash("Passwords don't match!")
        else:
            username_exists = Users.query.filter_by(username=username).first()
            email_exists = Users.query.filter_by(email=email).first()
            if username_exists or email_exists:
                flash('Username or email already exists!')
            else:
                new_user = Users(username=username, email=email, password=generate_password_hash(password1))
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                flash('Sign up successful', 'info')
                return redirect(url_for('views.personalize'))

    return render_template('register.html')
   

@views.route('/personalize', methods = ['GET', 'POST'])
def personalize():
    if request.method == "POST":
        age = request.form.get('age')
        language = request.form.get('language')
        subjects = request.form.get('subjects')
        if subjects:
            subjects = json.loads(subjects)
        id = current_user.id
        usercreds = UserPreferences(user_id = id, age = age, language = language, subjects=subjects)
        db.session.add(usercreds)
        db.session.commit()
        return redirect(url_for("views.home")) #CHANGE THIS TO DDOE HOME

    return render_template('personalize.html')
    #if request.method == 'POST':
    

@views.route('/chatbot', methods=['GET', 'POST'])
@login_required
def chatbot():
    if current_user.is_authenticated:
        print('logged in')
    if request.method == "POST":
        user = UserPreferences.query.filter_by(user_id=current_user.id).first()
        age = user.age
        language = user.language
        prompt = request.form.get("prompt")
        reply = gpt.chat(prompt, age, language)
        return render_template("chatbot.html", reply = reply)
    else:
        return render_template("chatbot.html")
    

@views.route('/dangerous')
def dangerous():
    
    users = Users.query
    for i in users:
        db.session.delete(i)
    
    db.session.commit()
    return render_template('dangerous.html')

@views.route('/createtest', methods = ['GET', 'POST'])
@login_required
def create_test():
    if(request.method == "POST"):
        userpref = UserPreferences.query.filter_by(user_id=current_user.id).first()
        topic = request.form.get("topic")
        session['testtopic'] = topic
        formats = request.form.get("format")
        return redirect(url_for("views.test", age=userpref.age, prompt=topic, formats=formats))
    return render_template("create_test.html")

@login_required
@views.route("/test", methods=['GET', 'POST'])
def test():
    if(request.method == "POST"):
        userans = []
        for i in range(len(session.get('questions'))):
            answer = request.form.get(f'answer{i}')
            userans.append(answer)
        session['userans'] = userans
        return redirect(url_for("views.checktest"))
    else:
        age = request.args.get('age')
        prompt = request.args.get('prompt')
        formats = request.args.get('formats')

        questions, choices, gptans = gpt.create_test(prompt, age, formats)
        questions = [item for item in questions if item.strip()]

        session['gptans'] = gptans
        session['format'] = formats
        session['questions'] = questions
        return render_template('test.html', questions=questions, choices = choices, formats = formats)

@login_required
@views.route("/checktest", methods=['GET', 'POST'])
def checktest():
    questions = session.get("questions")
    userans = session.get("userans")
    gptans = session.get("gptans")
    formats = session.get("format")
    topic = session.get("testtopic").split(" ")[0].strip().lower()
    correctans = gpt.checktest(userans, gptans, formats)
    gpt.testsandw(correctans, current_user.id, topic)
    return render_template('check_test.html', correctans = correctans, questions=questions)

@login_required
@views.route("/checksandw", methods=['GET', 'POST'])
def checksandw():
    userpref = UserPreferences.query.filter_by(user_id=current_user.id).first()
    userpref.strengths.append("mathematics")  # Correct spelling
    db.session.commit()  # Don't forget to commit the change to the database
    return render_template("checksandw.html", strengths=userpref.strengths, weaknesses=userpref.weaknesses)
    
@login_required
@views.route("/", methods=["GET", "POST"])
def home():
    today = datetime.now().date()
    ddoe = DDOE.query.filter_by(user_id=current_user.id).first()
    
    if not ddoe:
        ddoe = DDOE(user_id=current_user.id, last_updated=today)
        db.session.add(ddoe)
        db.session.commit()

    if ddoe.last_updated.date() == today:
        ddoe.last_updated = datetime.now()
        db.session.commit()
    else:
        ddoe.topic = gpt.ddoetopic(current_user.id, 0)
        ddoe.description = gpt.ddoedescription(current_user.id, ddoe.topic)
        ddoe.examples = gpt.ddoeexamples(current_user.id, ddoe.topic)
        db.session.commit()
    session['ddoetopic'] = ddoe.topic
    session['description'] = ddoe.description
    session['examples'] = ddoe.examples
    return render_template('home.html', topic=ddoe.topic, description=ddoe.description, examples=ddoe.examples)
    
@login_required
@views.route("/logout")
def logout():
    logout_user()
    session.clear()
    flash("Logged out successfully!")
    return redirect(url_for('views.login'))

@login_required
@views.route("/articles")
def articles():
    if 'ddoetopic' not in session:
        return redirect(url_for('views.home'))
    userpref = UserPreferences.query.filter_by(user_id=current_user.id).first()
    #the articles which are shown change everytime this page is reloaded
    article_list = []
    news_list = []
    ai_article_titles=['poop'] #To make sure chatgpt doesnt write repetitive articles.
    blog_list = [] 
    topic = session.get('ddoetopic')
    topic_keywords = gpt.keywords(topic) 
    print(topic_keywords)   
    news_titles, news_urls = ddoecontent.fetch_news_articles(topic_keywords, 10)
    blog_titles, blog_urls = ddoecontent.fetch_blog_articles(topic_keywords, 10)
    for i in range(0, 10):
        ai_article = gpt.ddoearticle(topic, userpref.age, ai_article_titles)
        try:
            if ai_article[1] is None or len(ai_article[1]) < 25:
                continue
            else:
                ai_article_titles.append(ai_article[0])
                article_list.append({'title': ai_article[0], 'text': ai_article[1]})
        except:
            continue
        
    for i in range(len(news_titles)): #Adding News Articles to 'article_list'
        news_text, news_media = ddoecontent.scrape_articles(news_urls[i])
        news_list.append({'title': news_titles[i], 'url': news_urls[i], 'text': news_text, 'media': news_media})
        article_list.append({'title': news_titles[i], 'url': news_urls[i], 'text': news_text, 'media': news_media})
    for i in range(len(blog_titles)): #Adding News Articles to 'article_list'
        blog_text, blog_media = ddoecontent.scrape_articles(blog_urls[i])
        blog_list.append({'title': blog_titles[i], 'url': blog_urls[i], 'text': blog_text, 'media': blog_media})
        article_list.append({'title': blog_titles[i], 'url': blog_urls[i], 'text': blog_text, 'media': blog_media})
    
    #MIGHT CHANGE IN THE FUTURE
    random.shuffle(article_list)
    # show articles as a popup.
    return render_template('articles.html', articles = article_list, news=news_list, blogs = blog_list)


        




#INACTIVE ROUTES

@login_required
@views.route("/navbar")
def navbar():
    return render_template('index.html')

@login_required
@views.route("/reels")
def reels():
    if 'ddoetopic' not in session:
        return redirect(url_for('views.home'))
    return render_template('index.html')

@login_required
@views.route("/account")
def account():
    return render_template('index.html')

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





