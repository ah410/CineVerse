# CineVerse
### Description
Allow users to find information on popular movies that are currently out. Quickly and easily access movie information.
### Demo: <[YouTube Showcase](https://youtu.be/FrbTbngjF1g)>
### Get Application Running/Unittesting
I'm using VS Code running Windows 10 for the below instructions.

*Note: You'll only be able to see the login and home page, but not the description page for the movies unless you created an API Key in the Google Cloud Console(it's free). This is because I used the YouTube Data API to fetch the trailer information from YouTube. For instructions on how to get your own API key, check this page on the Google API Python Client's [Github](https://github.com/googleapis/google-api-python-client/blob/main/docs/start.md). Additionally, you'll need to download the [Google Cloud SDK Installer](https://cloud.google.com/sdk/docs/install). Once you have your API Key, set an environment variable under User Variables with Name=`YouTube_API_KEY` and value=`your_actual_api_key_obtained_from_Google_Cloud_Console`. Here are instructions for setting an [environment variable](https://phoenixnap.com/kb/windows-set-environment-variable).  

*Only Python Versions before 3.12.0 work. I used python version `3.11.6`. Link for [python 3.11.6](https://www.python.org/downloads/release/python-3116/). If you've already created a venv, you'll need to delete it and create a new one so it updates the python version to the correct one.

1. Clone the repository
    1. Open command palette by clicking view in the top left, then command palette. Or `Ctrl+Shift+p`.
    2. Type welcome and click on Help: Welcome to bring up the welcome page
    3. Click on the option to clone git repository(if this option isn't showing up, you'll likely have to install [Git](https://git-scm.com) on your computer), then paste this URL: https://github.com/ah410/CineVerse 
2. Activate virtual env
    1. Once you've cloned the repo, navigate to its file path if you haven't already, and create your virtual environment. terminal: `python -m venv myenv`
    2. Activate your virtual environment by running this line in your terminal: `myenv/scripts/activate`
        1. If Windows isn't allowing scripts to run on your system. You'll need to open PowerShell as Administrator and run this line `Set-ExecutionPolicy RemoteSigned`
3. Install dependencies in requirements.txt(includes pytest for unittesting)
    1. Run this line in your terminal `pip install -r requirements.txt`
4. Type: `flask run` and the website should load up and you'll be good to go!
4. For unittesting, you can use the `pytest` library or the built in unittesting library for python, `unittest`
    1. Run unittests:
        1. terminal: `pytest app_test.py`
	    2. terminal: `python -m unittest app_test.py` 
### Features
#### Login/Sign-Up
The website automatically goes to the login page at the start. From there, you enter your username and password, hit enter/click the login button, and you'll be redirected to the homepage. However, if you don't have an account, I added a hyper-link and button to take you to the sign up page. From there, you'll create a username and password, which you'll confirm by entering twice. The username is stored in SQL as usual, but the password stored is a generated hash using the password created by the user as input to the generate_password_hash function from the werkzeug.security library.

#### Home Page
After logging in, the user will be greeted by a home page filled with movie poster images lined up row by row. Below each poster image is the corresponding movie title. Hovering over a movie item will enlarge the image and title, and removing your mouse will return the size back to normal. Each movie item is clickable, displaying a description page of the movie clicked. I used jinja to create a for loop of movie items that go through all the results of the movie table I created with SQL and TMDB's API.

#### Search
users search for movies on the top right of the website homepage. There is a search bar that takes a movie title as input and display all movies that match the spelling of that movie. I used SQL to run a search query using the wildcard '%' and the LIKE operator on my database of movies that was retrieved from TMDB. After the user presses enter on their keyboard or clicks the search button, a page will load displaying all the movies that fit the title entered in the search query by the user.

#### Description Page
This page contains an enlarged poster image, movie title, release date, description, and trailer. The trailer is shown using the iframe tag in HTML. Using Youtube's Data API V3 and the google-api-python-client library, I made a call to the Search function of the API.


### Technology Used
**Front-End:** HTML, CSS, JavaScript

**Back-End:** Python, Flask

**Database:** CS50's SQL, The Movie Database(TMDB) API, YouTube Data API V3

**Framework:** Bootstrap

**Libraries:** os, requests, flask, flask_session, datetime, cs50, werkzeug.security, functools, googleapiclient.discovery


### Challenges Faced
There were numerous issues I had to tackle, I'll go over them one by one.

#### Login Required re-direct:
I wanted to make it so if you try going to the website URL, it will redirect you to the login page, just like in week 9's pset. The code was already written for me in the finance code but I wanted to understand why it works. The solution was pretty advanced, using kwargs and args in Python so I referenced a tutorial. It's the 3rd video under references.

#### Figuring out how to use an API:
This was a good learning oppurtunity for me. I didn't really understand what an API was, so I first watched a quick explanation video on API's. Know knowing the basics, I looked up free databases for movies. The most popular one I found was themoviedatabase(TMDB). So I went through the setup process of creating an account and going to the API section of my account to create my API key. After that, I needed to figure out what I wanted from the database. After giving it some thought, I wanted to focus on popular movies. This led me to the API reference page of the developer section. Thankfully, TMDB's documentation is very extensive and intuitive. I found it very easy to find what I needed. The page explained the code I needed to add in Python and how to make a GET request to the API to fetch the movie list I need.

YouTube's API was also straightforward and easy to understand from their documentation, referenced in the 4th video under references. One thing I did differently for this API was using a 3rd party library. I did this because the googleapiclient library I used is officially supported by Google and makes my code a bit easier to understand and use. So, I had to read through both of their documentation. A good video I found on figuring out how to read and extract information from documentation can be found in the 10th video under references. The library documentation was a little overwhelming at first, but the getting started section broke things down.
1. Created a build object of yoututbe's data api v3, setting my api key to what I got from os.getenv() using the os library.
2. Searched and specified a list for the return, passing in the movie title followed by "trailer", and limited the result of the search to only 1, adding in .execute() at the end.
3. Now I need to search my list of dictionaries for the videoId, which is a unique identifier for using the watch query on YouTube. You can try this yourself by clicking on a YouTube video, and after v= is the unique videoId for that video. To find this, I went into the items dictionary, 0th index, id dictionary, and then the videoId key's value. This would look something like this in code, video_id = results['items'][0]['id']['videoId'].
4. To create the movie link, I used the embed URL from YouTube's IFrame player documentation. I added the video_id to the embed URL using format string.

#### The best way to display my homepage:
I struggled with the start of the project a lot. It mainly came down to the structure of my homepage and how best to do it. Some ideas I went through were grid layouts and tables. Each table data should have a movie poster image along with it's title underneath the image, similar to most streaming services. To make it 5 movie items per row, I set each movie item at 20% width. Also, in order to iterate over all the movies in the database, I used a jinja for loop. However, now I need a solution for actually clicking on the movie I want, extracting the info, and display a description of that movie. I tried adding a link, with the image as the clickable link, but kept getting an error message about the description page not loading. Then I thought back to what I learned in week 9. Submitting forms and buttons. Then it clicked. I'll wrap a button around the image and movie title. That button will be inside a form tag that will submit via POST to my index route. Additionally, I added in a hidden input with the value of the movie id in my homepage(index) html, allowing me to extract the correct movie's info the user clicked on. Now I had all the information I needed for the description page.

#### How to search for a YouTube movie trailer for the movie a user clicked on:
Starting off with a quick google search, I found selenium and beatiful soup for scrapping information on the internet. I tried various methods with beatiful soup but none worked. My theory is that YouTube's page dynamically loads content using JS so whatever information I could see using inspect element isn't the correct one I need. For selenium, it seemed that I needed to a webdriver. Both of these just didn't seem like the right fit for me. So, I kept searching and came across YouTube's Data V3 API. After some preliminary documentation reading, it had exactly what I needed. A search query with a way to get a link of a result of that search. Calling the API seemed confusing, but the documentation page mentioned the googleapiclient library that simplified the API calls. That's what I ended up using.


### Future Improvements
1. Favorite movies: Users can save movies to their favorites.
2. Advanced search: search by title, genre, rating, release year, etc.
3. User reviews and ratings: Allow users to rate and review movies. Let users view these rated movies and look at reviews other users submitted.
4. Add a sort by option on the homepage.


### References
1. API call request using TMDB's API: [Link to TMDB API Reference](https://developer.themoviedb.org/reference/movie-popular-list)
2. Base URL for image poster_path found on: [Link to TMDB discussion forum](https://www.themoviedb.org/talk/568e3711c3a36858fc002384)
3. google-api-python-client documentation: [Link to GitHub repository](https://github.com/googleapis/google-api-python-client/tree/main)
4. YouTube Data API V3 documentation: [Link to YouTube Data API V3 Documentation](https://developers.google.com/youtube/v3/docs/)
5. URL needed for embed YouTube videos using the iframe tag: [Link to YouTube IFrame Player Documentation](https://developers.google.com/youtube/player_parameters/#Manual_IFrame_Embeds)
6. Navbar tutorial using Bootstrap: [Link to YouTube tutorial](https://www.youtube.com/watch?v=qNifU_aQRio)
7. Bootstrap spacing classes: [Link to MDBootstrap documentation](https://mdbootstrap.com/docs/standard/utilities/spacing/)
8. Bootstrap color classes: [Link to MDBootstrap documentation](https://mdbootstrap.com/docs/standard/content-styles/colors/)
9. Login Required tutorial: [Login Required, Python Tutorial](https://www.youtube.com/watch?v=CD5lFKyH9Ls)
10. Python YouTube API tutorial: [Link to YouTube API tutorial](https://www.youtube.com/watch?v=th5_9woFJmk)
