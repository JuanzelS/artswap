"""
Tests for routes in ArtSwap application.
"""

import os
from unittest import TestCase
from models import db, User, ArtPiece, Trade

# Set up test database URI
os.environ['DATABASE_URL'] = "postgresql:///artswap_test"

from app import app, CURR_USER_KEY

# Disable WTForms CSRF validation in tests
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True
app.config['DEBUG'] = False

class RouteTestCase(TestCase):
    """Test routes for ArtSwap."""
    
    def setUp(self):
        """Create test client, add sample data."""
        
        # Drop and recreate tables
        db.drop_all()
        db.create_all()
        
        # Create test users
        self.user1 = User.signup(
            username="testuser1",
            email="test1@test.com",
            password="password"
        )
        
        self.user2 = User.signup(
            username="testuser2",
            email="test2@test.com",
            password="password"
        )
        
        db.session.commit()
        
        # Create test art pieces
        self.art1 = ArtPiece(
            title="Test Art 1",
            description="This is a test art piece",
            image_url="static/test_image1.jpg",
            user_id=self.user1.id
        )
        
        self.art2 = ArtPiece(
            title="Test Art 2",
            description="This is another test art piece",
            image_url="static/test_image2.jpg",
            user_id=self.user2.id
        )
        
        db.session.add_all([self.art1, self.art2])
        db.session.commit()
        
        # Create a test trade
        self.trade = Trade(
            sender_id=self.user1.id,
            receiver_id=self.user2.id,
            sender_art_id=self.art1.id,
            receiver_art_id=self.art2.id,
            status="pending"
        )
        
        db.session.add(self.trade)
        db.session.commit()
        
        # Create test client
        self.client = app.test_client()
    
    def tearDown(self):
        """Clean up any failed transactions."""
        db.session.rollback()
    
    def test_home_page(self):
        """Test home page route."""
        
        resp = self.client.get('/')
        html = resp.get_data(as_text=True)
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Welcome to ArtSwap", html)
        self.assertIn("Test Art 1", html)
        self.assertIn("Test Art 2", html)
    
    def test_signup_route(self):
        """Test user signup."""
        
        # Test GET request
        resp = self.client.get('/signup')
        html = resp.get_data(as_text=True)
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Create an Account", html)
        
        # Test POST request with valid data
        resp = self.client.post(
            '/signup',
            data={
                "username": "newuser",
                "email": "new@test.com",
                "password": "password",
                "confirm": "password"
            },
            follow_redirects=True
        )
        html = resp.get_data(as_text=True)
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Welcome, newuser!", html)
        
        # Verify user was created in database
        user = User.query.filter_by(username="newuser").first()
        self.assertIsNotNone(user)
    
    def test_login_route(self):
        """Test user login."""
        
        # Test GET request
        resp = self.client.get('/login')
        html = resp.get_data(as_text=True)
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Login", html)
        
        # Test POST request with valid credentials
        resp = self.client.post(
            '/login',
            data={
                "username": "testuser1",
                "password": "password"
            },
            follow_redirects=True
        )
        html = resp.get_data(as_text=True)
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Hello, testuser1!", html)
    
    def test_logout_route(self):
        """Test user logout."""
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
            
            resp = c.get('/logout', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("You have been logged out.", html)
            
            # Check that session no longer contains user_id
            with c.session_transaction() as sess:
                self.assertNotIn(CURR_USER_KEY, sess)
    
    def test_dashboard_route(self):
        """Test dashboard route."""
        
        # Test when not logged in
        resp = self.client.get('/dashboard', follow_redirects=True)
        html = resp.get_data(as_text=True)
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized", html)
        self.assertIn("Login", html)
        
        # Test when logged in
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
            
            resp = c.get('/dashboard')
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Your Dashboard", html)
            self.assertIn("Test Art 1", html)
    
    def test_new_art_route(self):
        """Test new art piece creation route."""
        
        # Test when not logged in
        resp = self.client.get('/art/new', follow_redirects=True)
        html = resp.get_data(as_text=True)
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized", html)
        
        # Test when logged in (GET request)
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
            
            resp = c.get('/art/new')
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Upload New Artwork", html)
    
    def test_art_detail_route(self):
        """Test art detail route."""
        
        # Test valid art piece
        resp = self.client.get(f'/art/{self.art1.id}')
        html = resp.get_data(as_text=True)
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Test Art 1", html)
        self.assertIn("This is a test art piece", html)
        
        # Test nonexistent art piece
        resp = self.client.get('/art/999999')
        self.assertEqual(resp.status_code, 404)
    
    def test_trade_accept_route(self):
        """Test accepting a trade."""
        
        # Test when not logged in
        resp = self.client.post(f'/trade/{self.trade.id}/accept', follow_redirects=True)
        html = resp.get_data(as_text=True)
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized", html)
        
        # Test when logged in as trade receiver
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user2.id
            
            resp = c.post(f'/trade/{self.trade.id}/accept', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Trade accepted", html)
            
            # Verify trade status was updated
            trade = Trade.query.get(self.trade.id)
            self.assertEqual(trade.status, "accepted")
    
    def test_trade_reject_route(self):
        """Test rejecting a trade."""
        
        # Test when logged in as trade receiver
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user2.id
            
            resp = c.post(f'/trade/{self.trade.id}/reject', follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Trade rejected", html)
            
            # Verify trade status was updated
            trade = Trade.query.get(self.trade.id)
            self.assertEqual(trade.status, "rejected")