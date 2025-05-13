"""
Main application file for ArtSwap.
"""

import os
from flask import Flask, render_template, redirect, url_for, flash, session, g, request, abort
# Debug toolbar import removed to avoid dependency issues
# from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
import uuid

from models import db, connect_db, User, ArtPiece, Trade
from forms import SignupForm, LoginForm, ArtPieceForm, TradeForm

CURR_USER_KEY = "curr_user"
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)

# Use SQLite instead of PostgreSQL for easier setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///artswap.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
# Debug toolbar config removed
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Make sure uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Debug toolbar initialization removed
# debug = DebugToolbarExtension(app)

connect_db(app)

# Create tables
with app.app_context():
    db.create_all()

##############################################################################
# User signup/login/logout

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup."""
    
    if g.user:
        return redirect(url_for('dashboard'))
        
    form = SignupForm()
    
    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data
            )
            db.session.commit()
            
        except IntegrityError:
            db.session.rollback()
            flash("Username already taken", 'danger')
            return render_template('auth/signup.html', form=form)
            
        do_login(user)
        flash(f"Welcome, {user.username}!", "success")
        return redirect(url_for('dashboard'))
        
    return render_template('auth/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""
    
    if g.user:
        return redirect(url_for('dashboard'))
        
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.authenticate(
            username=form.username.data,
            password=form.password.data
        )
        
        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect(url_for('dashboard'))
            
        flash("Invalid credentials.", 'danger')
        
    return render_template('auth/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""
    
    do_logout()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))


##############################################################################
# Homepage and dashboard

@app.route('/')
def home():
    """Show homepage with featured artwork."""
    
    # Get some recent artwork to display
    recent_art = ArtPiece.query.order_by(ArtPiece.created_at.desc()).limit(8).all()
    
    return render_template('home.html', recent_art=recent_art)


@app.route('/dashboard')
def dashboard():
    """Show user dashboard."""
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect(url_for('login'))
        
    # Get user's artwork
    user_art = ArtPiece.query.filter_by(user_id=g.user.id).all()
    
    # Get pending incoming trades
    incoming_trades = Trade.query.filter_by(
        receiver_id=g.user.id,
        status='pending'
    ).order_by(Trade.created_at.desc()).all()
    
    # Get pending outgoing trades
    outgoing_trades = Trade.query.filter_by(
        sender_id=g.user.id,
        status='pending'
    ).order_by(Trade.created_at.desc()).all()
    
    # Get trade history
    trade_history = Trade.query.filter(
        ((Trade.sender_id == g.user.id) | (Trade.receiver_id == g.user.id)) &
        (Trade.status != 'pending')
    ).order_by(Trade.updated_at.desc()).limit(10).all()
    
    return render_template(
        'users/dashboard.html',
        user_art=user_art,
        incoming_trades=incoming_trades,
        outgoing_trades=outgoing_trades,
        trade_history=trade_history
    )


##############################################################################
# Art piece routes

@app.route('/art/new', methods=["GET", "POST"])
def new_art():
    """Show form for uploading a new art piece."""
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect(url_for('login'))
        
    form = ArtPieceForm()
    
    if form.validate_on_submit():
        # Handle file upload
        file = form.image.data
        if file and allowed_file(file.filename):
            # Generate unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Create new art piece
            art = ArtPiece(
                title=form.title.data,
                description=form.description.data,
                image_url=file_path,
                user_id=g.user.id
            )
            
            db.session.add(art)
            db.session.commit()
            
            flash("Your artwork has been uploaded!", "success")
            return redirect(url_for('art_detail', id=art.id))
        else:
            flash("Invalid file type. Please upload an image file.", "danger")
    
    return render_template('art/new.html', form=form)


@app.route('/art/<int:id>')
def art_detail(id):
    """Show details of a specific art piece."""
    
    art = ArtPiece.query.get_or_404(id)
    
    # Check if user can offer trades for this piece
    can_trade = g.user and g.user.id != art.user_id and g.user.art_pieces
    
    # If user can trade, prepare the trade form
    trade_form = None
    if can_trade:
        trade_form = TradeForm()
        trade_form.sender_art_id.choices = [
            (piece.id, piece.title) for piece in g.user.art_pieces
        ]
        trade_form.receiver_art_id.data = art.id
    
    return render_template(
        'art/detail.html',
        art=art,
        can_trade=can_trade,
        trade_form=trade_form
    )


##############################################################################
# Trade routes

@app.route('/trade/new', methods=["POST"])
def new_trade():
    """Create a new trade offer."""
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect(url_for('login'))
    
    form = TradeForm()
    form.sender_art_id.choices = [
        (piece.id, piece.title) for piece in g.user.art_pieces
    ]
    
    if form.validate_on_submit():
        sender_art_id = form.sender_art_id.data
        receiver_art_id = form.receiver_art_id.data
        
        # Validate that the pieces exist and belong to the right users
        sender_art = ArtPiece.query.get_or_404(sender_art_id)
        receiver_art = ArtPiece.query.get_or_404(receiver_art_id)
        
        if sender_art.user_id != g.user.id:
            flash("You can only offer your own artwork.", "danger")
            return redirect(url_for('art_detail', id=receiver_art_id))
            
        if receiver_art.user_id == g.user.id:
            flash("You cannot trade with yourself.", "danger")
            return redirect(url_for('art_detail', id=receiver_art_id))
        
        # Check if this trade already exists
        existing_trade = Trade.query.filter_by(
            sender_id=g.user.id,
            receiver_id=receiver_art.user_id,
            sender_art_id=sender_art_id,
            receiver_art_id=receiver_art_id,
            status='pending'
        ).first()
        
        if existing_trade:
            flash("You already have a pending trade for this artwork.", "warning")
            return redirect(url_for('art_detail', id=receiver_art_id))
        
        # Create the trade
        trade = Trade(
            sender_id=g.user.id,
            receiver_id=receiver_art.user_id,
            sender_art_id=sender_art_id,
            receiver_art_id=receiver_art_id,
            status='pending'
        )
        
        db.session.add(trade)
        db.session.commit()
        
        flash("Trade offer sent!", "success")
        return redirect(url_for('dashboard'))
    
    flash("Invalid form data. Please try again.", "danger")
    return redirect(url_for('dashboard'))


@app.route('/trade/<int:id>/accept', methods=["POST"])
def accept_trade(id):
    """Accept a pending trade."""
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect(url_for('login'))
    
    trade = Trade.query.get_or_404(id)
    
    # Validate that the current user is the receiver
    if trade.receiver_id != g.user.id:
        flash("You are not authorized to accept this trade.", "danger")
        return redirect(url_for('dashboard'))
    
    # Validate that the trade is pending
    if not trade.is_pending:
        flash("This trade is no longer pending.", "warning")
        return redirect(url_for('dashboard'))
    
    # Update trade status
    trade.status = 'accepted'
    db.session.commit()
    
    flash("Trade accepted!", "success")
    return redirect(url_for('dashboard'))


@app.route('/trade/<int:id>/reject', methods=["POST"])
def reject_trade(id):
    """Reject a pending trade."""
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect(url_for('login'))
    
    trade = Trade.query.get_or_404(id)
    
    # Validate that the current user is the receiver
    if trade.receiver_id != g.user.id:
        flash("You are not authorized to reject this trade.", "danger")
        return redirect(url_for('dashboard'))
    
    # Validate that the trade is pending
    if not trade.is_pending:
        flash("This trade is no longer pending.", "warning")
        return redirect(url_for('dashboard'))
    
    # Update trade status
    trade.status = 'rejected'
    db.session.commit()
    
    flash("Trade rejected.", "info")
    return redirect(url_for('dashboard'))


##############################################################################
# Error handlers

@app.errorhandler(404)
def page_not_found(e):
    """404 NOT FOUND page."""
    
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True, port=5001) 