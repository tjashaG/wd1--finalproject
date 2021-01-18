import os
from sqla_wrapper import SQLAlchemy

db = SQLAlchemy(os.getenv("DATABASE_URL", "sqlite:///webapp.sqlite"))

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    secret_number = db.Column(db.Integer)
    attempts = db.Column(db.Integer)
    top_score = db.Column(db.Integer)
    games_played = db.Column(db.Integer)
    session_token = db.Column(db.String)
    deleted = db.Column(db.Boolean, default=False)
    city = db.Column(db.String, default="Ljubljana")
    signout_time = db.Column(db.String)


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(30))
    body = db.Column(db.String)
    timestamp = db.Column(db.String)

class Todo(db.Model):
    __tablename__ = "todos"
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String)
    owner = db.Column(db.Integer, db.ForeignKey('users.id'))
    due_date = db.Column(db.String)
    current_date = db.Column(db.String)
