import unittest
from unittest.mock import Mock,patch
from app import app, db
from bs4 import BeautifulSoup


class TestApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize datbase
        cls.db = db

    @classmethod
    def tearDownClass(cls):
        # Delete registered user from registration testing after each test run
        cls.db.execute("DELETE FROM users WHERE username = ?", 'user12')


    def setUp(self):
        # Create a test client
        self.app = app.test_client()

        
    @patch('app.requests.get')
    @patch('app.db.execute')
    def test_index_route_GET(self, mock_db_execute, mock_TMDB_request):
        # Make sure user is logged in
        with self.app.session_transaction() as session:
            session['user_id'] = 1
            session['logged_in'] = True

        # Mock TMDB API call, GET request
        mock_TMDB_request.status_code = 200
        mock_TMDB_request.json.return_value = [{
            "page": 1,
            "results": [
                {
                "adult": 'false',
                "backdrop_path": "/1syW9SNna38rSl9fnXwc9fP7POW.jpg",
                "genre_ids": [
                    28,
                    878,
                    12
                ],
                "id": 1,
                "original_language": "en",
                "original_title": "Spider-Man: Across the Spider-Verse",
                "overview": "After reuniting with Gwen Stacy, Brooklyn's full-time, friendly neighborhood Spider-Man is catapulted across the Multiverse, where he encounters the Spider Society, a team of Spider-People charged with protecting the Multiverse's very existence. But when the heroes clash on how to handle a new threat, Miles finds himself pitted against the other Spiders and must set out on his own to save those he loves most.",
                "popularity": 2972.534,
                "poster_path": "/poster_path_1.jpg",
                "release_date": "2023-05-31",
                "title": "Spider-Man: Across the Spider-Verse",
                "video": 'false',
                "vote_average": 7.2,
                "vote_count": 956
                },
            ]
        }]

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



    @patch('app.youtube')
    @patch('app.db.execute')
    def test_index_route_POST(self, mock_db_execute, mock_youtube_search):
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

        # Mock the YouTube API response using custom mock
        response_data = Mock(return_value= {"items": [{"id": {"kind":"youtube#video","videoId":"IHvzw4Ibuho"}}]})
        #print("This is the response data: ", response_data())
        mock_youtube_search().list.return_value.execute= response_data

        # POST request to index route
        response = self.app.post('/', follow_redirects=True)
        #print(response.data)
       
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
        response = self.app.post('/search')

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
