from flask import Flask, Blueprint, render_template, request, url_for, redirect, session, flash
from datetime import timedelta
from . import gpt

from . import app
views = Blueprint("views", __name__)


@views.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        age = int(request.form.get("age"))
        prompt = request.form.get("prompt")
        reply = gpt.chat(prompt, age)
        return render_template("test.html", reply = reply)
    else:
        return render_template("test.html", response = "")