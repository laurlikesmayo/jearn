from flask import Flask, Blueprint, render_template, request, url_for, redirect, session, flash, jsonify
from datetime import timedelta, datetime
from werkzeug.security import generate_password_hash, check_password_hash 
from .models import Users, UserPreferences, DDOE, SavedContent
from sqlalchemy.orm.attributes import flag_modified
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
    ddoe = DDOE.query
    pref = UserPreferences.query
    for i in users:
        db.session.delete(i)
    for i in ddoe:
        db.session.delete(i)
    for i in pref:
        db.session.delete(i)
    
    db.session.commit()
    return render_template('dangerous.html')

@views.route('/createtest', methods = ['GET', 'POST'])
@login_required
def create_test():
    if(request.method == "POST"):
        prompt = request.form.get("prompt")
        session['testprompt'] = prompt
        formats = request.form.get("format")
        return redirect(url_for("views.test", prompt=prompt, formats=formats))
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
        userpref = UserPreferences.query.filter_by(user_id=current_user.id).first()
        age = userpref.age
        prompt = request.args.get('prompt')
        if prompt == 'random':
            prompt = gpt.ddoetopic(current_user.id, random.randint(0, 3))
        formats = request.args.get('formats')

        questions, choices, gptans = gpt.create_test(prompt, age, formats)
        questions = [item for item in questions if item.strip()]
        for i in range(0, len(questions)):
            for j in range(0, i):
                try:
                    if "option" in choices[i][j].lower():
                        flash('An error has occured. Please try again.')
                        return redirect(url_for('views.create_test'))
                    
                except:
                    pass
            if "a)" in questions[i].lower():
                flash("An error has occured. Please try again.")
                return redirect(url_for('views.create_test'))
            

        session['gptans'] = gptans
        session['format'] = formats
        session['questions'] = questions
        session['testtopic'] = prompt
        return render_template('test.html', questions=questions, choices = choices, formats = formats)
    


@login_required
@views.route("/checktest", methods=['GET', 'POST'])
def checktest():
    questions = session.get("questions")
    userans = session.get("userans")
    gptans = session.get("gptans")
    formats = session.get("format")
    topic = session.get("testtopic").split(" ")[0].strip().lower()
    correctans = gpt.checktest(userans, gptans, formats, questions)
    score = gpt.testsandw(correctans, current_user.id, topic)
    return render_template('check_test.html', score = score, correctans = correctans, questions=questions)

@login_required
@views.route("/checksandw", methods=['GET', 'POST'])
def checksandw():
    userpref = UserPreferences.query.filter_by(user_id=current_user.id).first()
    current_strengths = userpref.strengths or []
    new_strength = 'WHats UP'
    if new_strength not in current_strengths:
        userpref.strengths.append(new_strength)

                # Update the user preferences with the new strengths
        #userpref.strengths = current_strengths
        db.session.commit()
        print("stregnth added successfully")
    
    return render_template("checksandw.html", strengths=userpref.strengths, weaknesses=userpref.weaknesses)
@login_required
@views.route("/", methods=["GET", "POST"])
def home():
    today = datetime.now().date()
    ddoe = DDOE.query.filter_by(user_id=current_user.id).first()
    if request.args.get('topic'):
        ddoe.topic=request.args.get('topic')
        topic = ddoe.topic
        ddoe.description = gpt.ddoedescription(current_user.id, topic)
        ddoe.examples=gpt.ddoeexamples(current_user.id, topic)
        db.session.commit()

    if not ddoe:
        topic = gpt.ddoetopic(current_user.id, 0)
        description = gpt.ddoedescription(current_user.id, topic)
        examples = gpt.ddoeexamples(current_user.id, topic)
        word = gpt.ddoeword(current_user.id)
        ddoe = DDOE(
            user_id=current_user.id, 
            topic=topic, 
            description=description, 
            examples=examples, 
            last_updated=today, 
            previous_topics=[topic], 
            word=word, 
            previous_words=[word],
            current_streak=1
        )
        db.session.add(ddoe)
        db.session.commit()
        print(f"New DDOE created: {ddoe}")

    if ddoe.last_updated != today or request.method == "POST":
        yesterday = today - timedelta(days=1)
        
        if ddoe.last_updated == yesterday:
            ddoe.current_streak += 1
        else:
            ddoe.current_streak = 1
        
        num = random.randint(0, 3)
    
        ddoe.topic = gpt.ddoetopic(current_user.id, num)
        ddoe.description = gpt.ddoedescription(current_user.id, ddoe.topic)
        ddoe.examples = gpt.ddoeexamples(current_user.id, ddoe.topic)
        ddoe.word = gpt.ddoeword(current_user.id)
        ddoe.definition = gpt.ddoedefinition(ddoe.word)
        ddoe.last_updated = today
        
        if not ddoe.previous_topics:
            ddoe.previous_topics = []
        if not ddoe.previous_words:
            ddoe.previous_words = []
        
        ddoe.previous_topics.append(ddoe.topic)
        ddoe.previous_words.append(ddoe.word)

        db.session.commit()
        print(f"{ddoe.topic}, {ddoe.previous_topics}, {ddoe.word}, {ddoe.last_updated}, {today}, {request.method}")

    session['ddoetopic'] = ddoe.topic
    session['description'] = ddoe.description
    session['examples'] = ddoe.examples
    
    return render_template('home.html', topic=ddoe.topic, description=ddoe.description, examples=ddoe.examples, word=ddoe.word, definition = ddoe.definition)
    

@login_required
@views.route('/previoustopics')
def previous_topics():
    ddoe = DDOE.query.filter_by(user_id=current_user.id).first()
    previous_topics = ddoe.previous_topics
    return render_template('prevtopic.html', previous_topics = previous_topics)
@login_required
@views.route("/logout")
def logout():
    logout_user()
    session.clear()
    flash("Logged out successfully!")
    print('loggedout')
    return redirect(url_for('views.login'))

@login_required
@views.route("/articles", methods = ['GET', 'POST'])
def articles():
    if request.method == 'POST':
        topic = request.form.get('topic')
        if topic == 'recommend':
            topic = gpt.ddoetopic(current_user.id, random.randint(0, 3))
    elif 'ddoetopic' in session:
        topic = session.get('ddoetopic') 
    else:
        return redirect(url_for('views.home'))
    articles = fetch_next(topic, decide=True)
    return render_template('articles.html', articles = articles, topic=topic)
    # news=news_list, blogs = blog_list,



@login_required
@views.route("/reels", methods = ['GET', 'POST'])
def reels():
    if request.method == 'POST':
        topic = request.form.get('topic')
        if topic == 'recommend':
            topic = gpt.ddoetopic(current_user.id, random.randint(0, 3))
        previous_topic = session.get('reels_previous_topic', '')
        
        if topic != previous_topic:
            # Reset the page token if the topic changes
            prev_npt = None
        else:
            # Use the existing page token if the topic is the same
            prev_npt = session.get('reels_npt', None)
        
        # Fetch results with the current topic and page token
        reels_list, npt = ddoecontent.fetch_youtubeshorts(topic, page_token=prev_npt,)
        
        # Update session with the current state
        session['reels_previous_topic'] = topic
        session['reels_npt'] = npt  # Store the new page token
        session['reels_list'] = reels_list
    elif 'ddoetopic' in session:
        topic = session.get('ddoetopic') 
        npt = session.get('reels_npt', None)
        reels_list, npt = ddoecontent.fetch_youtubeshorts(topic, page_token=npt)
        session['reels_previous_topic'] = topic
        session['reels_npt'] = npt
        session['reels_list'] = reels_list
    else:
        return redirect(url_for('views.home'))

    return render_template('reels.html', reels_list=reels_list, topic=topic)

@login_required
@views.route('/testing')
def randomx():
    ddoe = DDOE.query.filter_by(user_id = current_user.id).first()
    for i in range(0, 10):
        print(gpt.ddoetopic(current_user.id, 0))
        print(ddoe.previous_topics)
        print(gpt.ddoeword(current_user.id))
    return render_template('index.html')

@login_required
@views.route("/account")
def account():
    ddoe = DDOE.query.filter_by(user_id=current_user.id).first()
    user = Users.query.filter_by(id=current_user.id).first()
    current_streak = ddoe.current_streak
    return render_template('account.html', current_streak=current_streak, user=user)


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
    blog_titles, blog_urls = ddoecontent.fetch_blog_articles(topic_keywords, 1)  # Fetch 2 blog articles
    
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
def find_articles(topic):
    userpref = UserPreferences.query.filter_by(user_id=current_user.id).first()
    #the articles which are shown change everytime this page is reloaded
    article_list = []
    news_list = []
    ai_article_titles=['poop'] #To make sure chatgpt doesnt write repetitive articles.
    blog_list = [] 
    topic_keywords = gpt.keywords(topic) 
    print(topic_keywords)   
    news_titles, news_urls = ddoecontent.fetch_news_articles(topic_keywords, 10)
    blog_titles, blog_urls = ddoecontent.fetch_blog_articles(topic_keywords, 10)
    for i in range(0, 5):
        ai_article = gpt.ddoearticle(topic, userpref.age, ai_article_titles)
        try:
            if ai_article[1] is None or len(ai_article[1]) < 25:
                continue
            else:
                ai_article_titles.append(ai_article[0])
                article_list.append({'title': ai_article[0], 'text': ai_article[1]})
        except:
            continue
        
    try:
        for i in range(len(news_titles)): #Adding News Articles to 'article_list'
            if ddoecontent.is_embeddable(news_urls[i]):
                news_text, news_media = ddoecontent.scrape_articles(news_urls[i])
                news_list.append({'title': news_titles[i], 'url': news_urls[i], 'text': news_text, 'media': news_media})
                article_list.append({'title': news_titles[i], 'url': news_urls[i], 'text': news_text, 'media': news_media})
    except:
        pass
    try:
        for i in range(len(blog_titles)): #Adding News Articles to 'article_list'
            if ddoecontent.is_embeddable(blog_urls[i]):
                blog_text, blog_media = ddoecontent.scrape_articles(blog_urls[i])
                blog_list.append({'title': blog_titles[i], 'url': blog_urls[i], 'text': blog_text, 'media': blog_media})
                article_list.append({'title': blog_titles[i], 'url': blog_urls[i], 'text': blog_text, 'media': blog_media})
    except:
        pass
        
    #MIGHT CHANGE IN THE FUTURE
    random.shuffle(article_list)

    return article_list, news_list, blog_list

@login_required
@app.route('/save_note', methods=['POST'])
def save_note():
    data = request.get_json()
    video_id = data['video_id']
    note_content = data['note']
    video_title = data.get('video_title', 'Unknown Title')
    new_note = SavedContent(
        user_id = current_user.id,
        title=video_title,
        content=video_id,
        note = note_content
    )
    db.session.add(new_note)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Note saved successfully'})


@app.route('/see_note')
def see_note():
    notes = SavedContent.query.filter_by(user_id = current_user.id)
    for i in notes:
        print(i.note)
    return redirect(url_for('views.home'))


#INACTIVE ROUTES

@login_required
@views.route("/navbar")
def navbar():
    return render_template('index.html')


@views.route('sidebar')
def js():
    return render_template('sidebar.html')

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





