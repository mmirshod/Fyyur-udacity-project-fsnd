from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app import app

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Genre(db.Model):
    __tablename__ = "Genre"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String())


artist_genre = db.Table(
    "artist_genre",
    db.Column("genre_id", db.ForeignKey("Genre.id")),
    db.Column("artist_id", db.ForeignKey("Artist.id"))
)

venue_genre = db.Table(
    "venue_genre",
    db.Column("genre_id", db.ForeignKey("Genre.id")),
    db.Column("venue_id", db.ForeignKey("Venue.id"))
)


class Venue(db.Model):
    __tablename__ = "Venue"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String())
    shows = db.relationship("Show", backref="venue", lazy=False)
    genres = db.relationship("Genre", secondary=venue_genre, lazy=False)
    seeking_talents = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String())


class Artist(db.Model):
    __tablename__ = "Artist"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    shows = db.relationship("Show", backref="artist", lazy=False)
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(255))
    website_link = db.Column(db.String(255))
    genres = db.relationship("Genre", secondary=artist_genre, lazy=False)


class Show(db.Model):
    __tablename__ = "Show"

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey("Venue.id"), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey("Artist.id"), nullable=False)
    time = db.Column(db.DateTime, nullable=False)
