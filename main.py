from flask import Flask, render_template, make_response, redirect, flash, url_for, request
from models import db, User, Message, Todo
import hashlib
import random
from uuid import uuid4
import requests
import os
import time


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
db.create_all()

@app.route("/", methods=["GET", "POST"])
def sign_up():

    session_token = request.cookies.get("session_token")
    req = request.form
    #if there's a session token,
    #user gets redirected to the login page
    if session_token:
        user = db.query(User).filter_by(session_token=session_token, deleted=False)
        return redirect(url_for("login", user=user))

    #if user posts on signup form, a new user gets created
    if request.method == "POST":
        if not db.query(User).filter_by(email=req.get("email")).first():
            session_token = str(uuid4())
            username = req.get("username")
            email = req.get("email")
            p_word = req.get("password")
            password = hashlib.sha256(p_word.encode()).hexdigest()
            secret_number = random.randint(1, 100)
            attempts = 0
            top_score = 100
            games_played = 0
            signout_time = time.strftime(r"%d.%m.%Y %H:%M", time.localtime())
            user = User(username=username, email=email, password=password, secret_number=secret_number,
                        attempts=attempts, games_played=games_played, session_token=session_token,
                        top_score=top_score, deleted=False, signout_time=signout_time)
            db.add(user)
            db.commit()

            res = make_response(redirect(url_for("profile")))
            res.set_cookie("session_token", session_token)
            return res
        #if the email exists in the database, it will not let the user sign-up
        else:
            message = "Email already exists in database!"
            flash(message)
            return render_template("sign-up.html")

    return render_template("sign-up.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    req = request.form
    # the login handler will also check if user.deleted is False. If it's set to True
    # (meaning the user deleted their profile), it will tell user they aren't registered

    if request.method == "POST":
        email = req.get("email")
        p_word = req.get("password")
        password = hashlib.sha256(p_word.encode()).hexdigest()
        user = db.query(User).filter_by(email=email, deleted=False).first()

        if user:
            if email == user.email:
                if password == user.password:
                    res = make_response(redirect(url_for("profile")))
                    res.set_cookie("session_token", user.session_token)
                    return res
                else:
                    message = "Wrong username or password"
                    flash(message)
        else:
            message = "You are not a registered user. Please sign-in!"
            flash(message)
    return render_template("login.html")

@app.route("/profile", methods=["GET"])
def profile():
    OPENWEATHER_API = "https://api.openweathermap.org/data/2.5/weather"
    API_KEY = os.getenv("OPENWEATHER_API_KEY")
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()
    location = user.city

    r = requests.get(f"{OPENWEATHER_API}?q={location}&units=metric&appid={API_KEY}")
    data = r.json()

    temperature = data["main"]["temp"]
    weather = data["weather"][0]["description"]  # because it's an array
    feels_like = data["main"]["feels_like"]

    return render_template("user.html", user=user, temperature=temperature,
                           location=user.city, weather=weather, feels_like=feels_like)

#deletes the session token and thus returns to sign-up page
@app.route("/sign-out")
def sign_out():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()
    current_time = time.strftime(r"%d.%m.%Y %H:%M", time.localtime())
    user.signout_time = current_time
    db.add(user)
    db.commit()
    #user.signout_time is for the 'new message' function
    res = make_response(redirect(url_for("sign_up")))
    res.delete_cookie("session_token")
    return res

@app.route("/profile/messages", methods=["POST", "GET"])
def messages():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()
    timestamp = None

    if request.method == "POST":
        recipient = db.query(User).filter_by(email=request.form.get("email")).first()
        if recipient:
            title = request.form.get("title")
            body = request.form.get("body")
            recipient_id = recipient.id
            sender_id = user.id
            timestamp = time.strftime(r"%d.%m.%Y %H:%M", time.localtime())
            message = Message(sender_id=sender_id, recipient_id=recipient_id,
                              title=title, body=body, timestamp=timestamp)
            db.add(message)
            db.commit()
            flash(message="Message sent successfully")

        else:
            flash(message="This recipient does not exist! Check the address and try again")

    messages = db.query(Message).filter_by(recipient_id=user.id).all()
    sender = None

    for message in messages:
        sender_id = message.sender_id
        sender = db.query(User).filter_by(id=sender_id).first()
        if user.signout_time < message.timestamp:
            flash(message="You have a new message")
            user.signout_time = time.strftime(r"%d.%m.%Y %H:%M", time.localtime())
            db.add(user)
            db.commit()


    return render_template("messages.html", messages=messages, sender=sender, time=timestamp)


@app.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    req = request.form
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()
    if request.method == "POST":
        if req.get("username"):
            user.username = req.get("username")
        if req.get("email"):
            user.email = req.get("email")
        if req.get("password"):
            p_word = req.get("password")
            p_word_again = req.get("password-again")

            if p_word == p_word_again:
                password = hashlib.sha256(p_word.encode()).hexdigest()
                user.password = password
            else:
                flash(message="The passwords don't match")

        if req.get("country"):
            user.country = req.get("country")
        if req.get("city"):
            user.city = req.get("city")

        db.add(user)
        db.commit()
        res = make_response(redirect(url_for("profile")))
        return res
    return render_template("edit_profile.html", user=user)

@app.route("/profile/delete", methods=["GET", "POST"])
def delete_profile():
    return render_template("profile_delete.html")

#if user confirms and deletes their profile,
#they don't get removed from the database, but the 'user.deleted' is True
#and the session token gets deleted
@app.route("/profile/delete/confirmed")
def profile_delete_confirmed():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()
    user.deleted = True
    db.add(user)
    db.commit()
    res = make_response(redirect(url_for("sign_up")))
    res.delete_cookie("session_token")
    return res

@app.route("/recover-profile", methods=["GET", "POST"])
def recover_profile():

    if request.method == "POST":
        req = request.form
        email = req.get("email")
        p_word = req.get("password")
        password = hashlib.sha256(p_word.encode()).hexdigest()
        user = db.query(User).filter_by(email=email, deleted=True).first()
        #to recover profile, user must input the username and password.
        #If they are correct, 'user.deleted' is switched back to False
        if user:
            if user.password == password:
                user.deleted = False
                db.add(user)
                db.commit()
                flash(message="Your profile was successfully restored! Yay!")
                res = make_response(redirect(url_for("profile")))
                res.set_cookie("session_token", user.session_token)
                return res
            else:
                flash(message="Wrong password")
        else:
            flash(message="Sorry, the email wasn't found in our database")

    return render_template("recover_profile.html")

@app.route("/todo", methods=["POST", "PUT", "DELETE", "GET"])
def to_do():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()
    if request.method == "POST":
        if user:
            task = request.form.get("task")
            due_date = request.form.get("due_date")
            date_pretty = due_date.split("-")
            final_date = date_pretty[2] + "-" + date_pretty[1] + "-" + date_pretty[0]
            todo = Todo(task=task, due_date=final_date, owner=user.id)
            db.add(todo)
            db.commit()
            flash(message="Task successfully added")

    todos = db.query(Todo).filter_by(owner=user.id).all()
    return render_template("todo.html", todos=todos)

@app.route("/game", methods=["GET", "POST"])
def game():

    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()

    if request.method == "POST":
        guess = int(request.form.get("guess"))
        user_secret = int(user.secret_number)

        if guess == user_secret:
            flash(message=f"Correct! The secret number was {user_secret}")
            new_secret = random.randint(1, 100)
            user.secret_number = str(new_secret)
            user.games_played += 1
            user.attempts += 1
            flash(message=f"You needed {user.attempts} guesses!")

            if user.attempts < user.top_score:
                user.top_score = user.attempts

            user.attempts = 0
            db.add(user)
            db.commit()
            print(user.secret_number)
            return render_template("game.html", guess=True)
        elif guess > user_secret:
            user.attempts += 1
            db.add(user)
            db.commit()
            flash(message="Lower")
        else:
            user.attempts += 1
            db.add(user)
            db.commit()
            flash(message="Higher")

    return render_template("game.html")

@app.route("/news", methods=["GET"])
def news_api():
    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    url = f'http://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}'
    response = requests.get(url)
    cleared = response.json()

    articles = cleared["articles"]

    article_titles = []

    for article in articles:
        title = article["title"]
        url = article["url"]
        author = article["author"]
        description = article["description"]
        img_url = article["urlToImage"]
        article_titles.append((title, url, author, description, img_url))

    return render_template("news.html", article_titles=article_titles)
