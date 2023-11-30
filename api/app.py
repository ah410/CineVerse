import os
import requests
import psycopg2

from flask import Flask, flash, render_template, request, session, redirect, url_for
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from googleapiclient.http import HttpMock
from googleapiclient.discovery import build
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# Set secret key
secret_key = os.getenv("SECRET_KEY")
app.config['SECRET_KEY'] = secret_key

# Configure the app to use sessions
app.config["SESSION_PERMANENT"] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.permanent_session_lifetime = timedelta(minutes=60)
Session(app)

# Get TMDB API_KEY from environment variables
api_key = os.getenv("TMDB_API_KEY")

# Get YouTube API_KEY from environment variables and start a build
yt_api_key = os.getenv("YouTube_API_KEY")
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

# Get postgres url and set up connection
postgres_url = os.getenv("POSTGRES_URL")
app.config['SQLALCHEMY_DATABASE_URI'] = postgres_url
db = SQLAlchemy(app)

# Create users table
# db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL)")
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    hashed_password = db.Column(db.String(255), nullable=False)

class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    overview = db.Column(db.String(255), nullable=False)
    release_date = db.Column(db.String(255), nullable=False)
    poster_path = db.Column(db.String(255), nullable=False)

with app.app_context():
    db.create_all()


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


@app.route("/", methods = ['GET', 'POST'])
@login_required
def index():
    if request.method == "GET":
        # Make a GET request to the TMDB API to fetch a list of popular movies
        response = requests.get(f'https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=en-US&page=1', headers=headers)

        # Extract the list of popular movies into a json file from the response the API gave, access the results dictionary
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
            # db.execute("INSERT OR IGNORE INTO movies (id, title, overview, release_date, poster_path) VALUES (?, ?, ?, ?, ?)", id, title, overview, release_date, poster_path)

            # Only add movie to the db if the movie is not already added
            if not Movies.query.filter_by(id=id).all():
                new_movie = Movies(id=id, title=title, overview=overview, release_date=release_date, poster_path=poster_path)
                db.session.add(new_movie)
                db.session.commit()


        # Query the database(returns a list of dict objects, each of which represents a row in the result)
        # movies = db.execute("SELECT * FROM movies ORDER BY release_date DESC")
        movies = Movies.query.all()

        # Return index.html and pass movies SQL database into it
        return render_template("index.html", movies = movies, URL = base_poster_path_URL)

    elif request.method == "POST":
        # Get movie info from movie_id that was submitted in the form
        # movie = db.execute("SELECT * FROM movies WHERE id = ?", request.form.get("movie_id"))[0]
        movie = Movies.query.filter_by(id=request.form.get("movie_id")).first()

        # Search youtube build object and get back a list, passing in movie title the user clicked and set number of results = 1, set parameter part to snippet
        results = youtube.search().list(part='snippet', q=f'{movie.title} trailer', maxResults=1).execute()

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
        # results = db.execute("SELECT * FROM movies WHERE title LIKE '%' || ? || '%'", search)
        results = Movies.query.filter(Movies.title.ilike(f"%{search}%")).all()

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

        # rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        user = Users.query.filter_by(username=username).first()

        # Ensure username exists and password is correct
        if not user or not check_password_hash(user.hashed_password, password):
            return render_template("apology.html", text="invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = user.id
        session["logged_in"] = True

        # Redirect the user to the homepage to view movies
        return redirect("/")

    # User reached the route via GET(clicking on link or redirect)
    elif request.method=="GET":
        return render_template("login.html")

# Set the appropriate response headers for the session cookie
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    response.headers["Set-Cookie"] = "HttpOnly;Secure;SameSite=None"
    return response


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
        # rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        user = Users.query.filter_by(username=username).first()
        if user is not None:
            text = "Username already exists"
            return render_template("apology.html", text=text)

        # Generate password hash
        hash = generate_password_hash(password)

        # Store user's info in database
        # db.execute("INSERT INTO users (username, password) VALUES (?,?)", username, hash)
        new_user = Users(username=username, hashed_password=hash)
        db.session.add(new_user)
        db.session.commit()

        # Log user in
        # id_new_user = db.execute("SELECT id FROM users WHERE password = ?", hash)
        session["user_id"] = new_user.id

        # Log user in and Redirect user to homepage
        session["logged_in"] = True
        return redirect("/")

    # User reached the route via GET(clicking on link or redirect)
    elif request.method == "GET":
        return render_template("register.html")
    

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)