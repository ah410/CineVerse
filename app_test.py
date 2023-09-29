import unittest
import os
from unittest.mock import Mock, patch
from app import app, db
from flask import request
from flask_login import login_user
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from bs4 import BeautifulSoup

class TestApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ["FLASK_ENV"] = "testing"

        # Initialize datbase
        cls.db = db

    @classmethod
    def tearDownClass(cls):
        # Delete registered user from registration testing after each test run
        cls.db.execute("DELETE FROM users WHERE username = ?", 'user12')

        # Clear the environment variable after each test run
        os.environ.pop("FLASK_ENV", None)

    def setUp(self):
        # Create a test client
        self.app = app.test_client()

        

    @patch('app.db.execute')
    def test_index_route_GET(self, mock_db_execute):
        # Make sure user is logged in
        with self.app.session_transaction() as session:
            session['user_id'] = 1
            session['logged_in'] = True

        # Mock database SELECT query
        mock_db_execute.return_value = [
            {'id': 1, 
             'title': 'Spider-Man: Across the Spider-Verse', 
             'overview': "After reuniting with Gwen Stacy, Brooklyn's full-time, friendly neighborhood Spider-Man is catapulted across the Multiverse, where he encounters the Spider Society, a team of Spider-People charged with protecting the Multiverse's very existence. But when the heroes clash on how to handle a new threat, Miles finds himself pitted against the other Spiders and must set out on his own to save those he loves most.", 
             'release_date': '2023-05-31', 
             'poster_path': '/poster_path_1.jpg'}
        ]

        # Mock base poster path and set query parameters
        mock_base_poster_path = 'http://image.tmdb.org/t/p/w185'
        query_parameters = {'movies': mock_db_execute(), 'URL': mock_base_poster_path}

        # GET request to index route
        response = self.app.get('/', query_string=query_parameters, follow_redirects=True)

        # Assert that the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Assert that you're on the home page(index.html)
        soup = BeautifulSoup(response.data, 'html.parser')
        home_page = soup.find('h1')
        home_page_text = home_page.text.strip()
        self.assertEqual(home_page_text, 'Home Page')

        # Assert that index.html is putting the correct database information
        movie_title = soup.find('p', {'class': 'movie_title'})
        movie_title_text = movie_title.text.strip()
        self.assertEqual(movie_title_text, 'Spider-Man: Across the Spider-Verse')



    @patch('app.db.execute')
    def test_index_route_POST(self, mock_db_execute):
        # Make sure user is logged in
        with self.app.session_transaction() as session:
            session['user_id'] = 1
            session['logged_in'] = True

        # Mock database SELECT query
        mock_db_execute.return_value = [
            {'id': 2, 
             'title': 'Teenage Mutant Ninja Turtles: Mutant Mayhem', 
             'overview': "After years of being sheltered from the human world, the Turtle brothers set out to win the hearts of New Yorkers and be accepted as normal teenagers through heroic acts. Their new friend April O'Neil helps them take on a mysterious crime syndicate, but they soon get in over their heads when an army of mutants is unleashed upon them.", 
             'release_date': '2023-07-31', 
             'poster_path': '/poster_path_3.jpg'}
        ]

        # Mock poster URL
        mock_large_poster_path = 'http://image.tmdb.org/t/p/w342'

        # Mock movie link(TMNT Mutant Mayhem), IHvzw4Ibuho = video_id(return value of youtube search using YT_DATA_API)
        mock_movie_link = 'https://www.youtube.com/embed/IHvzw4Ibuho'

        # Define query parameters as a dictionary
        query_parameters = {'movie': mock_db_execute(), 'URL': mock_large_poster_path, 'movie_link': mock_movie_link}

        # POST request to index route
        response = self.app.post('/', query_string=query_parameters, follow_redirects=True)
       
        # Assert that the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Assert that index.html is showing correct database information
        soup = BeautifulSoup(response.data, 'html.parser')
        movie_title = soup.find('p')
        movie_title_text = movie_title.text.strip()
        self.assertEqual(movie_title_text, 'Movie title: Teenage Mutant Ninja Turtles: Mutant Mayhem')
        


    @patch('app.db.execute')
    def test_search_route_no_results(self, mock_db_execute):
        # Make sure user is logged in
        with self.app.session_transaction() as session:
            session['user_id'] = 1
            session['logged_in'] = True

        # Mock database execution, empty list since no matches found
        mock_db_execute.return_value = []
        
        # Mock base poster path and set query parameters
        mock_base_poster_path = 'http://image.tmdb.org/t/p/w185'
        query_parameters = {'movies': mock_db_execute, 'URL': mock_base_poster_path}

        # POST request to search route
        response = self.app.post('/search', query_string=query_parameters)

        # Assert that the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Assert that you're on apology.html since no results were found in the search
        soup = BeautifulSoup(response.data, 'html.parser')
        error_message = soup.find('div', {'label': 'errorMessage'})
        error_message_text = error_message.text.strip()
        self.assertEqual(error_message_text, 'Sorry, no results found.')


    @patch('app.db.execute')
    def test_search_route_results(self, mock_db_execute):
        # Make sure user is logged in
        with self.app.session_transaction() as session:
            session['user_id'] = 1
            session['logged_in'] = True

        # Mock database execution
        mock_db_execute.return_value = [{'id': 2, 
             'title': 'Barbie', 
             'overview': 'Barbie and Ken are having the time of their lives in the colorful and seemingly perfect world of Barbie Land. However, when they get a chance to go to the real world, they soon discover the joys and perils of living among humans.', 
             'release_date': '2023-07-19', 
             'poster_path': '/poster_path_2.jpg'}]
        
        # Mock base poster path and set query parameters
        mock_base_poster_path = 'http://image.tmdb.org/t/p/w185'
        query_parameters = {'movies': mock_db_execute, 'URL': mock_base_poster_path}

        # POST request to search route
        response = self.app.post('/search', query_string=query_parameters)

        # Assert that the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Assert that index.html is showing the correct search information 
        soup = BeautifulSoup(response.data, 'html.parser')
        movie_title = soup.find('p',{'class':'movie_title'})
        self.assertEqual(movie_title.text.strip(), 'Barbie')


    def test_login_route_GET(self):
        # Send a GET request to the /login route
        response = self.app.get('/login')

        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Assert that you're on login.html
        soup = BeautifulSoup(response.data, 'html.parser')
        title_tag = soup.find('title')
        title_text = title_tag.text.strip()
        self.assertEqual(title_text, 'Login') 
        
        # Assert that username field is there
        username = soup.find('label', {'for': 'username'})
        username_text = username.text
        self.assertEqual(username_text, 'Username')

        # Assert that password field is there
        password = soup.find('label', {'for': 'password'})
        password_text = password.text
        self.assertEqual(password_text, 'Password')



    def test_successful_login_route_POST(self):
        # POST request to login, user10 is already in database
        response = self.app.post('/login', data={
            'username': 'user10',
            'password': 'password10'
        }, follow_redirects=True)

        # Assert that response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)  

         # Parse the content to make sure user is on home page, index.html
        soup = BeautifulSoup(response.data, 'html.parser')
        home_header = soup.find('h1')
        self.assertEqual(home_header.text.strip(), 'Home Page')



    def test_successful_logout(self):
        # Make GET request to the logout route
        response = self.app.get('/logout', follow_redirects=True)

        # Assert that response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)
        
        # Parse the content to make sure page redirects to the login page
        soup = BeautifulSoup(response.data, 'html.parser')
        login_header = soup.find('h2', {'class':'text-center'})
        self.assertEqual(login_header.text.strip(), 'Login')



    def test_registration_route_GET(self):
        # Make GET request to the register route
        response = self.app.get('/register')

        # Assert that response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Check that user is on register.html page
        soup = BeautifulSoup(response.data, 'html.parser')
        header2 = soup.find('h2')
        header2_text = header2.text.strip()
        self.assertEqual(header2_text, 'Sign up')

       

    def test_successful_registration_route_POST(self):
        # Mock username and password
        username = 'user12'
        password = 'password12'
        confirm_password = 'password12'

        # Simulate successful registration by adding the correct data to the POST request
        response = self.app.post('/register', data = {
            'username': username,
            'password': password,
            'confirm_password': confirm_password
        }, follow_redirects=True)

        # Check that the response code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Parse the content to assert that you're on the home page, index.html
        soup = BeautifulSoup(response.data, 'html.parser')
        home_page = soup.find('h1')
        home_page_text = home_page.text.strip()
        self.assertEqual(home_page_text, 'Home Page')

        

    def test_unsuccessful_username_registration_route_POST(self):
        # Mock username and password
        password = 'password1'
        confirm_password = 'password1'

        # Simulate registration attempt by adding the incorrect data to the POST request
        response = self.app.post('/register', data = {
            'username': '',
            'password': password,
            'confirm_password': confirm_password
        })

        # Check that the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Parse the content to assert that you're on apology.html, text should say 'No username entered'
        soup = BeautifulSoup(response.data, 'html.parser')
        error_message = soup.find('div', {'label': 'errorMessage'})
        error_message_text = error_message.text.strip()
        self.assertEqual(error_message_text, 'No username entered')      



    def test_unsuccessful_password_registration_route_POST(self):
        # Mock username and password
        username = 'User56'
        confirm_password = 'password1'

        # Simulate registration attempt by adding the incorrect data to the POST request
        response = self.app.post('/register', data = {
            'username': username,
            'password': '',
            'confirm_password': confirm_password
        })

        # Check that the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Parse the content to assert that you're on apology.html, text should say 'No password entered'
        soup = BeautifulSoup(response.data, 'html.parser')
        error_message = soup.find('div', {'label': 'errorMessage'})
        error_message_text = error_message.text.strip()
        self.assertEqual(error_message_text, 'No password entered')    
