"""
Seed file to make sample data for ArtSwap db.
"""

from app import db
from models import User, ArtPiece, Trade

# Drop all tables
db.drop_all()

# Create all tables
db.create_all()

# Add users
alice = User.signup(
    username="alice",
    email="alice@example.com",
    password="password"
)

bob = User.signup(
    username="bob",
    email="bob@example.com",
    password="password"
)

charlie = User.signup(
    username="charlie",
    email="charlie@example.com",
    password="password"
)

diana = User.signup(
    username="diana",
    email="diana@example.com",
    password="password"
)

db.session.commit()

# Add art pieces
art1 = ArtPiece(
    title="Sunset Dreams",
    description="A digital painting of a sunset over mountains",
    image_url="static/uploads/sample_sunset.jpg",
    user_id=alice.id
)

art2 = ArtPiece(
    title="Cyberpunk City",
    description="Futuristic cityscape with neon lights",
    image_url="static/uploads/sample_cyberpunk.jpg",
    user_id=alice.id
)

art3 = ArtPiece(
    title="Fantasy Warrior",
    description="Character concept art of a fantasy warrior",
    image_url="static/uploads/sample_warrior.jpg",
    user_id=bob.id
)

art4 = ArtPiece(
    title="Underwater World",
    description="Detailed digital art of an underwater scene",
    image_url="static/uploads/sample_underwater.jpg",
    user_id=bob.id
)

art5 = ArtPiece(
    title="Abstract Minds",
    description="Abstract digital art with vibrant colors",
    image_url="static/uploads/sample_abstract.jpg",
    user_id=charlie.id
)

art6 = ArtPiece(
    title="Space Explorer",
    description="Astronaut exploring a new planet",
    image_url="static/uploads/sample_space.jpg",
    user_id=charlie.id
)

art7 = ArtPiece(
    title="Forest Spirit",
    description="Mystical creature in an enchanted forest",
    image_url="static/uploads/sample_forest.jpg",
    user_id=diana.id
)

art8 = ArtPiece(
    title="Urban Sketch",
    description="Digital sketch of a modern city street",
    image_url="static/uploads/sample_urban.jpg",
    user_id=diana.id
)

db.session.add_all([art1, art2, art3, art4, art5, art6, art7, art8])
db.session.commit()

# Add trades
trade1 = Trade(
    sender_id=alice.id,
    receiver_id=bob.id,
    sender_art_id=art1.id,
    receiver_art_id=art3.id,
    status="pending"
)

trade2 = Trade(
    sender_id=charlie.id,
    receiver_id=alice.id,
    sender_art_id=art5.id,
    receiver_art_id=art2.id,
    status="pending"
)

trade3 = Trade(
    sender_id=bob.id,
    receiver_id=diana.id,
    sender_art_id=art4.id,
    receiver_art_id=art7.id,
    status="accepted"
)

trade4 = Trade(
    sender_id=diana.id,
    receiver_id=charlie.id,
    sender_art_id=art8.id,
    receiver_art_id=art6.id,
    status="rejected"
)

db.session.add_all([trade1, trade2, trade3, trade4])
db.session.commit()

print("Database seeded!")