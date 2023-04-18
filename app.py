# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import re
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import os
from flask_migrate import Migrate
from datetime import datetime
from operator import itemgetter

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


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
    

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    data = []
    locs = set()

    for venue in Venue.query.all():
        locs.add((venue.city, venue.state))

    locs = list(locs)
    locs.sort(key=itemgetter(1, 0))
    now = datetime.now()

    for loc in locs:
        loc_venues = []
        for venue in loc_venues:
            if venue.city == loc[0] and venue.state == loc[1]:
                venue_shows = Show.query.filter_by(venue_id=venue.id).all()
                num_upcom_shows = 0
                for show in venue_shows:
                    if show.time > now:
                        num_upcom_shows += 1

                loc_venues.append({
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": num_upcom_shows
                })
        data.append({
            "city": loc[0],
            "state": loc[1],
            "venues": loc_venues
        })

    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    search_result = Venue.query.filter(Venue.name.ilike(f"%{request.form.get('search_term', '')}%"))
    data = []
    now = datetime.now()
    for venue in search_result:
        venue_shows = Show.query.filter_by(venue_id=venue.id).all()
        num_upcom_shows = 0
        for show in venue_shows:
            if show.time > now:
                num_upcom_shows += 1

        data.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": num_upcom_shows
        })

    response = {
        "count": len(data),
        "data": data
    }

    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).first()
    if not venue:
        abort(404)  # User typed url by him/herself

    now = datetime.now()
    upcoming_shows = []
    past_shows = []

    for show in venue.shows:
        show_data = {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.time))
        }

        if show.date > now:
            upcoming_shows.append(show_data)
        else:
            past_shows.append(show_data)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": [genre.name for genre in venue.genres],
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talents,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template("pages/show_venue.html", venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    form = VenueForm()
    if not form.validate():
        flash(form.errors)
        return redirect(url_for('create_venue_form'))

    error = False
    try:
        new_venue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=re.sub('\D', '', form.phone.data),
            image_link=form.image_link.data,
            website_link=form.website_link.data,
            seeking_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data
        )
        for genre in form.genres.data:
            form_genre = Genre.query.filter_by(type=genre).one_or_none()
            if form_genre:
                new_venue.genres.append(form_genre)
            else:
                new_genre = Genre(type=genre)
                db.session.add(new_genre)
                new_venue.genres.append(new_genre)

        db.session.add(new_venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        flash("Error occurred while creating new venue" + request.form["name"])
    else:
        flash("Venue " + request.form["name"] + " was successfully listed!")

    return render_template("pages/home.html")


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).one_or_none()
    if not venue:
        abort(500)

    try:
        db.session.delete(venue)
        db.session.commit()
    except:
        abort(500)
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for("index"))


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    data = []
    all_artists = Artist.query.all()

    for artist in all_artists:
        formatted_data = {
            "id": artist.id,
            "name": artist.name
        }
        data.append(formatted_data)

    return render_template("pages/artists.html", artists=data)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    search_term = request.form.get("search_term", "")
    found_data = Artist.filter(Artist.name.ilike(f"%{search_term}%")).all()
    data = []

    now = datetime.now()
    for artist in found_data:
        artist_shows = Show.filter_by(artist_id=artist.id)
        num_upcom_shows = 0
        for show in artist_shows:
            if show.time > now:
                num_upcom_shows += 1
        data.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": num_upcom_shows
        })

    response = {
        "count": len(data),
        "data": data
    }

    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    artist = Artist.query.filter_by(id=artist_id)
    if not artist:
        abort(404)

    upcoming_shows = []
    past_shows = []
    now = datetime.now()

    for show in artist.shows:
        show_data = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.time
        }
        if show.time > now:
            upcoming_shows.append(show_data)
        else:
            past_shows.append(show_data)

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": [genre.name for genre in artist.genres],
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "facebook_link": artist.facebook_link,
        "website": artist.website_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
    }

    return render_template("pages/show_artist.html", artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    artist = Artist.query.filter_by(id=artist_id)
    if not artist:
        abort(404)

    form = ArtistForm(obj=artist)

    artist = {
        "id": artist.id,
        "name": artist.name,
        "genres": [genre.name for genre in artist.genres],
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "image_link": artist.image_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description
    }

    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    form = ArtistForm()
    if not form.validate():
        flash(form.errors)
        return redirect(url_for("index"))

    flag = False
    try:
        # Get new genres' list:
        genres = []
        for genre in form.genres.data:
            inputted_genre = Genre.query.filter_by(type=genre)
            if inputted_genre:
                genres.append(inputted_genre)
            else:
                new_genre = Genre(type=genre)
                db.session.add()
                genres.append(new_genre)


        artist = Artist.query.filter_by(id=artist_id)

        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = re.sub('\D', '', form.phone.data)
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data
        artist.facebook_link = form.facebook_link.data
        artist.website_link = form.website_link.data
        artist.image_link = form.image_link.data
        artist.genres = genres

        db.session.commit()
    except:
        flag = True
        db.session.rollback()
    finally:
        db.session.close()

    if not flag:
        flash("Artist has been updated!")
        return redirect(url_for("show_artist", artist_id=artist_id))
    else:
        flash("Error while updating artist!")
        return redirect(url_for("index"))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id)
    if not venue:
        abort(404)

    form = VenueForm(obj=venue)
    venue = {
        "id": venue.id,
        "name": venue.name,
        "genres": [genre.name for genre in venue.genres],
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talents,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
    }

    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    form = VenueForm()

    if not form.validate():
        flash("Error Occurred")
        return redirect(url_for('index'))

    flag = False
    try:
        # Get new genres
        genres = []

        for genre in form.genres.data:
            inputted_genre = Genre.query.filter_by(type=genre)
            if inputted_genre:
                genres.append(inputted_genre)
            else:
                new_genre = Genre(name=genre)
                db.session.add(new_genre)
                genres.append(new_genre)

        venue = Venue.query.filter_by(id=venue_id)
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = re.sub('\D', '', form.phone.data)
        venue.genres = genres
        venue.image_link = form.image_link.data
        venue.facebook_link = form.facebook_link.data
        venue.website = form.website_link.data
        venue.seeking_talents = form.seeking_talent
        venue.seeking_description = form.seeking_description

        db.session.commit()
    except:
        db.session.rollback()
        flag = True
    finally:
        db.session.close()

    if flag:
        flash("error while updating venue!")
        return redirect(url_for("index"))
    else:
        flash("venue updated successfully!")
        return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    form = ArtistForm()
    flag = False

    if not form.validate():
        flash(form.errors)
        return redirect(url_for("index"))

    try:
        genres = []
        for genre in form.genres.data:
            fetch_genre = Genre.query.filter_by(type=genre)
            if fetch_genre:
                genres.append(fetch_genre)
            else:
                new_genre = Genre(type=genre)
                db.session.add(new_genre)
                genres.append(new_genre)

        artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=re.sub('\D', '', form.phone.data),
            image_link=form.image_link.data.strip(),
            facebook_link=form.facebook_link.data.strip(),
            seeking_venue=form.seeking_venue.data,
            seeking_description=form.seeking_description.data.strip(),
            website=form.website_link.data.strip(),
            genres=genres
        )
        db.session.add(artist)
        db.session.commit()
    except:
        flag = True
        db.session.rollback()
    finally:
        db.session.close()

    if not flag:
        flash("Artist " + request.form["name"] + " was successfully listed!")
        return render_template("pages/home.html")
    else:
        flash("Error Occurred while creating artist!")
        return redirect(url_for("index"))


#  Shows
#  ----------------------------------------------------------------

@app.route("/shows")
def shows():
    all_shows = Show.query.all()
    data = []
    for show in all_shows:
        show_data = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.time,
        }
        data.append(show_data)

    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    form = ShowForm()
    if not form.validate():
        flash(form.errors)
        return redirect(url_for("index"))

    flag = False
    try:
        show = Show(
            time=form.start_time.data,
            artist_id=form.artist_id.data,
            venue_id=form.venue_id.data
        )
        db.session.add(show)
        db.session.commit()
    except:
        flag = True
        db.session.rollback()
    finally:
        db.session.close()

    if not flag:
        flash("Show was successfully listed!")
        return render_template("pages/home.html")
    else:
        flash("error occurred while creating show")
        return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
