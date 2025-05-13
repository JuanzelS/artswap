"""
Database models for ArtSwap application.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    """User model for authentication and profile information."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    # Keep using user_id but specify foreign_keys to avoid ambiguity
    art_pieces = db.relationship('ArtPiece', 
                                foreign_keys='ArtPiece.user_id',
                                backref='owner', 
                                lazy=True,
                                cascade="all, delete-orphan")
    
    # Add relationship for original creations
    original_creations = db.relationship('ArtPiece',
                                       foreign_keys='ArtPiece.original_creator_id',
                                       backref='creator',
                                       lazy=True)
    
    sent_trades = db.relationship('Trade', 
                                 foreign_keys='Trade.sender_id',
                                 backref='sender', 
                                 lazy=True)
    received_trades = db.relationship('Trade', 
                                     foreign_keys='Trade.receiver_id',
                                     backref='receiver', 
                                     lazy=True)
    
    @classmethod
    def signup(cls, username, email, password):
        """Sign up a new user. Hashes password and returns new user."""
        
        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')
        
        user = User(
            username=username,
            email=email,
            password_hash=hashed_pwd
        )
        
        db.session.add(user)
        return user
    
    @classmethod
    def authenticate(cls, username, password):
        """Authenticate user with username and password.
        
        Returns user if valid; otherwise returns False.
        """
        
        user = cls.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            return user
        
        return False
    
    def __repr__(self):
        return f"<User #{self.id}: {self.username}>"


class ArtPiece(db.Model):
    """Model for digital artwork."""
    
    __tablename__ = 'art_pieces'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255), nullable=False)
    
    # Keep user_id for existing database compatibility
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # New field for original creator
    original_creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    traded = db.Column(db.Boolean, default=False)
    
    # Relationships for trades
    offered_in_trades = db.relationship('Trade',
                                      foreign_keys='Trade.sender_art_id',
                                      backref='offered_art',
                                      lazy=True)
                                      
    requested_in_trades = db.relationship('Trade',
                                        foreign_keys='Trade.receiver_art_id',
                                        backref='requested_art',
                                        lazy=True)
    
    def was_acquired_through_trade(self):
        """Check if this art piece was acquired through trade."""
        return self.traded
    
    def previous_owner(self):
        """Get the previous owner of this artwork if it was traded."""
        if self.original_creator_id and self.original_creator_id != self.user_id:
            return User.query.get(self.original_creator_id)
        return None
    
    def __repr__(self):
        return f"<ArtPiece #{self.id}: {self.title}>"
    
    
class Trade(db.Model):
    """Model for trades between users."""
    
    __tablename__ = 'trades'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender_art_id = db.Column(db.Integer, db.ForeignKey('art_pieces.id'), nullable=False)
    receiver_art_id = db.Column(db.Integer, db.ForeignKey('art_pieces.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Trade #{self.id}: {self.status}>"
    
    @property
    def is_pending(self):
        """Check if the trade is pending."""
        return self.status == 'pending'
    
    @property
    def is_accepted(self):
        """Check if the trade is accepted."""
        return self.status == 'accepted'
    
    @property
    def is_rejected(self):
        """Check if the trade is rejected."""
        return self.status == 'rejected'

def connect_db(app):
    """Connect this database to provided Flask app."""
    db.app = app
    db.init_app(app)