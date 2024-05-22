from flask import Flask, Blueprint, render_template, request, url_for, redirect, session, flash
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash 
from .models import Users
from . import gpt

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
            session['loggedin'] = True
            flash('sign up sucessful', 'info')
            return redirect(url_for('views.personalize'))
    return render_template('register.html')    
    
@views.route('/personalize', methods = ['GET', 'POST'])
def personalize():
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
        return render_template("test.html", reply = reply)
    else:
        return render_template("test.html", response = "")