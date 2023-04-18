import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://" \
                          f"{os.getenv('DB_USER', 'postgres')}:" \
                          f"{os.getenv('DB_PASSWORD')}@" \
                          f"{os.getenv('DB_HOST', '127.0.0.1:5000')}/" \
                          f"{'DB_NAME', 'fyyur'}"

