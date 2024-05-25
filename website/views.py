from flask import Flask, Blueprint, render_template, request, url_for, redirect, session, flash, jsonify
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash 
from .models import Users, UserPreferences
from flask_login import login_user, logout_user, login_required, UserMixin, current_user
from . import gpt
import json

from . import app, db
views = Blueprint("views", __name__)


@views.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        username_exists = Users.query.filter_by(username = username).first()
        email_exists = Users.query.filter_by(email = email).first()
        if password1 != password2:
            flash("Passwords don't match!")
        elif username_exists or email_exists:
            flash('username or email already exists!')
        elif len(password1) < 6 or len(username) <6:
            flash("Username or password must contain more than 6 characters")
        else:
            new_user = Users(username = username, email=email, password=generate_password_hash(password1))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            session['loggedin'] = True
            flash('sign up sucessful', 'info')
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
        return redirect(url_for(views.home))

    return render_template('personalize.html')
    #if request.method == 'POST':

@views.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        age = request.form.get("age")
        print(age)
        prompt = request.form.get("prompt")
        language = request.form.get("language")
        reply = gpt.chat(prompt, age, language)
        return render_template("home.html", reply = reply)
    else:
        return render_template("home.html", response = "")
    
@views.route('/test', methods = ['GET', 'POST'])
def test():
