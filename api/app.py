import os
import requests

from flask import Flask, flash, render_template, request, session, redirect, url_for
from flask_session import Session
from datetime import timedelta
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from googleapiclient.http import HttpMock
from googleapiclient.discovery import build
from dotenv import load_dotenv


################################################################# SETUP ###################################################################################


app = Flask(__name__)
load_dotenv()

# Get OS environment variables
secret_key = os.getenv("SECRET_KEY")
api_key = os.getenv("TMDB_API_KEY")
yt_api_key = os.getenv("YouTube_API_KEY")

# Configure the app to use sessions
app.config['SECRET_KEY'] = secret_key
app.config["SESSION_PERMANENT"] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.permanent_session_lifetime = timedelta(minutes=60)
Session(app)

# Set the appropriate response headers for the session cookie
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    response.headers["Set-Cookie"] = "HttpOnly;Secure;SameSite=None"
    return response

# Get YouTube API_KEY from environment variables and start a build
if yt_api_key != None:
    youtube = build('youtube', 'v3', developerKey=yt_api_key)
else:
    http = HttpMock('config/youtube-discovery.json', {'status': '200'})
    api_key = 'your_api_key'
    service = build('youtube', 'v3', http=http, developerKey=api_key)
    youtube = service.search().list(part='snippet', q='Spider-Man: Across the Spider-Verse trailer', maxResults=1).execute()
    http = HttpMock('config/youtube-android.json', {'status': '200'})

# Add header from TMDB API Documentation
headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzNzJkYWI3M2FmZmExMzU4ZWI1MmM2NzI0ZTRiMTZkNSIsInN1YiI6IjY0NTU2NGIyNGU2NzQyMDE2NDU2YjU3OCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.padsDkjh_CPT1leQ5xT4of_1D2lCcPccBwRpvgm7B3A"
}

base_poster_path_URL = 'http://image.tmdb.org/t/p/w185'
large_poster_path_URL = 'http://image.tmdb.org/t/p/w342'

# Configure CS50 Library to use SQLite database
if os.environ.get("FLASK_ENV") == "testing":
    db = SQL("sqlite:///test.db")
else:
    db = SQL("sqlite:///../database/database.db")

# Create users table
db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL)")

# Define login_required function that requires login for home page and logout route
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for("login"))
    return wrap


################################################################# END SETUP ###############################################################################


@app.route("/", methods = ['GET', 'POST'])
@login_required
def index():
    if request.method == "GET":
        # Make a GET request to the TMDB API for popular movies and extract into json file
        response = requests.get(f'https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=en-US&page=1', headers=headers)
        movies = response.json()['results']

        # Results dictionary is a list of dictionaries, so loop through each index of dictionaries using a for loop, and in each index, access the keys I need using ["key"]
        for movie in movies:
            # Variables
            id = movie["id"]
            title = movie["title"]
            overview = movie["overview"]
            release_date = movie["release_date"]
            poster_path = movie["poster_path"]

            # Insert into movies table the values of each movie
            db.execute("INSERT OR IGNORE INTO movies (id, title, overview, release_date, poster_path) VALUES (?, ?, ?, ?, ?)", id, title, overview, release_date, poster_path)

        # Query the database (returns a list of dict objects, each of which represents a row in the result), return index.html and pass movies SQL database into it
        movies = db.execute("SELECT * FROM movies ORDER BY release_date DESC")
        return render_template("index.html", movies = movies, URL = base_poster_path_URL)

    elif request.method == "POST":
        # Get movie info from movie_id that was submitted in the form
        movie = db.execute("SELECT * FROM movies WHERE id = ?", request.form.get("movie_id"))[0]

        # Search youtube build object and get back a list, passing in movie title the user clicked and set number of results = 1, set parameter part to snippet
        results = youtube.search().list(part='snippet', q=f'{movie["title"]} trailer', maxResults=1).execute()

        # Find video ID of the results query
        video_id = results['items'][0]['id']['videoId']

        # Now that we have YouTube video ID, use embed URL to link to the video in the iFrame tag
        movie_link = f'https://www.youtube.com/embed/{video_id}'
        return render_template("description.html", movie = movie, URL = large_poster_path_URL, movie_link = movie_link)


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    # User reached route via POST
    if request.method == "POST":
        # Get user submitted search query
        search = request.form.get("search")

        # Check if any matches in database using LIKE to search for patterns either before or after user's search query
        results = db.execute("SELECT * FROM movies WHERE title LIKE '%' || ? || '%'", search)

        # If match was found, return index.html with found movies info. Else, return not found
        if not results:
            return render_template("apology.html", text="Sorry, no results found.")
        else:
            return render_template("index.html", movies = results, URL = base_poster_path_URL)


@app.route("/login", methods=["GET","POST"])
def login():
    # Forget user_id
    session.clear()

    # User reached route via POST
    if request.method == "POST":
        # Make variables
        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username was submitted
        if not username:
            return render_template("apology.html", text="must enter username")

        # Ensure password was submitted
        elif not password:
            return render_template("apology.html", text="must enter password")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], password):
            return render_template("apology.html", text="invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["logged_in"] = True

        # Redirect the user to the homepage to view movies
        return redirect("/")

    # User reached the route via GET(clicking on link or redirect)
    elif request.method=="GET":
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    # Forget any user_id and set logged in equal to false
    session.clear()
    session["logged_in"] = False

    # Redirect user to login form
    return redirect("/login")


@app.route("/register", methods=["GET","POST"])
def register():
    # User reached route via POST
    if request.method == "POST":
        # Make variables
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Ensure something was typed for username/password
        if not username:
            text = "No username entered"
            return render_template("apology.html", text=text)
        elif not password:
            text = "No password entered"
            return render_template("apology.html", text=text)
        elif not confirm_password:
            text = "Please confirm password"
            return render_template("apology.html", text=text)
        elif password != confirm_password:
            text = "Passwords don't match"
            return render_template("apology.html", text=text)

        # Check if username exists
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) != 0:
            text = "Username already exists"
            return render_template("apology.html", text=text)

        # Generate password hash
        hash = generate_password_hash(password)

        # Store user's info in database
        db.execute("INSERT INTO users (username, password) VALUES (?,?)", username, hash)

        # Log user in
        id_new_user = db.execute("SELECT id FROM users WHERE password = ?", hash)
        session["user_id"] = id_new_user[0]["id"]

        # Log user in and Redirect user to homepage
        session["logged_in"] = True
        return redirect("/")

    # User reached the route via GET(clicking on link or redirect)
    elif request.method == "GET":
        return render_template("register.html")