from flask import Flask, Blueprint, render_template, request, url_for, redirect, session, flash, jsonify
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash 
from .models import Users, UserPreferences
from flask_login import login_user, logout_user, login_required, UserMixin, current_user
from . import gpt
import json

from . import app, db
views = Blueprint("views", __name__)
@views.route('/login',  methods=['GET', 'POST'] )
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        permanentsesh =request.form.get('permanentsession')
        user = Users.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=user.email)
                print('Logged in')
                if permanentsesh:
                    session.permanent = True
                else:
                    session.permanent = False
                session['loggedin'] = True
                session['email'] = user.email
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
                session['loggedin'] = True
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
        return redirect(url_for("views.home"))

    return render_template('personalize.html')
    #if request.method == 'POST':
    
@login_required
@views.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        user = UserPreferences.query.filter_by(user_id=current_user.id)
        age = user.age
        language = user.language
        prompt = request.form.get("prompt")
        reply = gpt.chat(prompt, age, language)
        return render_template("home.html", reply = reply)
    else:
        return render_template("home.html")
    

@views.route('/dangerous')
def dangerous():
    
    users = Users.query
    for i in users:
        db.session.delete(i)
    
    db.session.commit()
    return render_template('dangerous.html')
    
@views.route('/createtest', methods = ['GET', 'POST'])
def create_test():
    if(request.method == "POST"):
        userpref = UserPreferences.query.filter_by(user_id=current_user.id)
        prompt = request.form.get("prompt")
        subject = request.form.get("subject")
        formats = request.form.get("format")
        return redirect(url_for("views.test", age=userpref.age, prompt=prompt, formats=formats, subject=subject))
    return render_template("create_test.html")

@views.route("test", methods=['GET', 'POST'])
def test(age, prompt, formats, subject):
    questions, answers = gpt.maketest(prompt, subject, age, formats)
    return render_template('test.html', questions=questions, formats = formats, answers=answers)

